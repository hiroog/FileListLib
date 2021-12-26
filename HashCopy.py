# 2021/12/21 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

import sys
import os
import re
import hashlib
import shutil
import time
from multiprocessing import Pool

sys.path.append( os.path.dirname( sys.argv[0] ) )
import FileListLib

#------------------------------------------------------------------------------

class HashDB:

    def __init__( self ):
        self.hash_map= {}
        self.new_hash_map= {}
        self.key_pat= re.compile( r'^([a-f0-9]+)\s+(.*)$' )

    def load( self, file_name ):
        if not file_name:
            return  None
        hash_map= {}
        if os.path.exists( file_name ):
            with open( file_name, 'r', encoding='utf-8' ) as fi:
                for line in fi:
                    line= line.strip()
                    if line == '' or line[0] == '#':
                        continue
                    pat= self.key_pat.search( line )
                    if pat:
                        value= pat.group( 1 )
                        key= pat.group( 2 )
                        hash_map[key]= value
        self.hash_map= hash_map
        return  self

    def save( self, file_name ):
        with open( file_name, 'w', encoding='utf-8' ) as fo:
            for key in self.hash_map:
                fo.write( '%s %s\n' % (self.hash_map[key], key) )

    def get_hash( self, hash_key ):
        if hash_key in self.hash_map:
            return  self.hash_map[hash_key]
        return  'NONE'

    def find_hash( self, hash_key ):
        if hash_key in self.hash_map:
            return  self.hash_map[hash_key]
        return  None

    def update( self, hash_key, hash_value ):
        self.hash_map[hash_key]= hash_value
        self.new_hash_map[hash_key]= hash_value

    def merge( self, src_hash ):
        for key in src_hash.new_hash_map:
            self.hash_map[key]= src_hash.new_hash_map[key]


class HashCopy:

    def __init__( self, dcache, scache ):
        self.dcache= dcache
        self.scache= scache

    def get_name_key( self, file_name ):
        return  os.path.abspath( file_name ).replace('\\','/').lower()

    def get_file_hash( self, file_name ):
        with open( file_name, 'rb' ) as fi:
            h= hashlib.sha1( fi.read() )
            return  h.hexdigest()

    def get_src_hash( self, file_name ):
        if self.scache:
            src_key= self.get_name_key( file_name )
            src_hash= self.scache.find_hash( src_key )
            if src_hash:
                return  src_hash
            src_hash= self.get_file_hash( file_name )
            self.scache.update( src_key, src_hash )
            return  src_hash
        return  self.get_file_hash( file_name )

    def copy_single( self, src_file, dest_file ):
        dest_key= self.get_name_key( dest_file )
        if os.path.exists( dest_file ):
            src_stat= os.stat( src_file )
            dest_stat= os.stat( dest_file )
            if src_stat.st_mtime < dest_stat.st_mtime:
                print( 'SkipT ', dest_file )
                return
            src_hash= self.get_src_hash( src_file )
            if src_stat.st_size == dest_stat.st_size and src_hash == self.dcache.get_hash( dest_key ):
                print( 'SkipH ', dest_file )
                return
            if (dest_stat.st_mode & 0o202) == 0:
                os.chmod( dest_file, dest_stat.st_mode | 0o606 )
        else:
            src_hash= self.get_src_hash( src_file )
        dest_path= os.path.dirname( dest_file )
        if dest_path != '' and not os.path.exists( dest_path ):
            try:
                os.makedirs( dest_path )
            except FileExistsError:
                pass
        print( 'copy', src_file, dest_file )
        for stime in range(3):
            try:
                shutil.copyfile( src_file, dest_file )
            except OSError:
                print( 'retry' )
                time.sleep( 1<<stime )
                continue
            break
        self.dcache.update( dest_key, src_hash )

    def copy_tupple_list( self, copy_list ):
        for src_name,dest_name in copy_list:
            self.copy_single( src_name, dest_name )


class CopyJob:
    def __init__( self, options, job_id ):
        self.options= options
        self.dcache= HashDB().load( self.options['dcache'] )
        self.scache= HashDB().load( self.options['scache'] )
        self.hash_copy= HashCopy( self.dcache, self.scache )
        self.job_id= job_id

    def copy_proc( self, copy_list ):
        self.hash_copy.copy_tupple_list( copy_list )
        return  self.dcache


class ParallelCopy:

    def __init__( self, options ):
        self.options= options
        self.dcache= HashDB().load( self.options['dcache'] )
        self.scache= HashDB().load( self.options['scache'] )
        self.hash_copy= HashCopy( self.dcache, self.scache )

    def finalize( self ):
        self.dcache.save( self.options['dcache'] )

    def __enter__( self ):
        return  self

    def __exit__( self, *arg ):
        self.finalize()

    def f_copy_single( self ):
        self.hash_copy.copy_single( self.options['src'], self.options['dest'] )

    def get_src_list( self, root ):
        fll= FileListLib.FileListLib( self.options['ignore'] )
        file_list= fll.find_file( root )
        return  file_list

    def split_list( self, param_list, num ):
        size= (len(param_list)//num+1)
        result= []
        base= 0
        for pi in range(num):
            ret= param_list[base:base+size]
            result.append( ret )
            base+= size
        return  result

    def f_copy( self ):
        parallel= self.options['parallel']
        src_root= self.options['src']
        dest_root= self.options['dest']
        ext_set= self.options['ext']
        use_ext= self.options['use_ext']
        file_list= self.get_src_list( src_root )
        src_len= len( src_root ) + 1
        copy_list= []
        for file_name in file_list:
            if use_ext:
                _,ext= os.path.splitext( file_name )
                if ext.lower() not in ext_set:
                    continue
            dest_name= os.path.join( dest_root, file_name[src_len:] )
            copy_list.append( (file_name, dest_name) )


        if parallel == 1:
            self.hash_copy.copy_tupple_list( copy_list )
        else:
            param_list= self.split_list( copy_list, parallel )
            result_list= []
            with Pool( parallel ) as pool:
                for pi in range(parallel):
                    job= CopyJob( self.options, pi )
                    result_list.append( pool.apply_async( job.copy_proc, (param_list[pi],) ) )

                for ret in result_list:
                    dcache= ret.get()
                    self.dcache.merge( dcache )


#------------------------------------------------------------------------------

def usage():
    print( 'HashCopy v1.00 2021 Hiroyuki Ogasawara' )
    print( 'usage: HashCopy [<options>] <command>' )
    print( 'options:' )
    print( '--ignore <ignore_file>' )
    print( '--src <src_dir>' )
    print( '--dest <dest_dir>' )
    print( '--ext <ext>             (ex. --ext .txt)' )
    print( '--dcache <dest_cache_file>' )
    print( '--scache <src_cache_file>' )
    print( '--parallel <num_threads>' )
    print( 'command:' )
    print( '--copy_single' )
    print( '--copy' )
    print( 'ex. python HashCopy.py --src ../bin --dest bin2 --copy --ext .exe' )
    sys.exit( 1 )

def getarg( ai, argv, options, optname ):
    if ai+1 < len(argv):
        ai+= 1
        options[optname]= argv[ai]
    return  ai


def main( argv ):
    options= {  
            'cmd'   : None,
            'src'   : None,
            'dest'  : None,
            'ignore': None,
            'ext'   : set(),
            'use_ext': False,
            'dcache' : 'file_cache.txt',
            'scache' : None,
            'parallel' : max( os.cpu_count(), 4 ),
        }
    ai= 1
    acount= len(argv)
    while ai < acount:
        arg= argv[ai]
        if arg[0] == '-':
            if arg == '--src':
                ai= getarg( ai, argv, options, 'src' )
            elif arg == '--dest':
                ai= getarg( ai, argv, options, 'dest' )
            elif arg == '--dcache':
                ai= getarg( ai, argv, options, 'dcache' )
            elif arg == '--scache':
                ai= getarg( ai, argv, options, 'scache' )
            elif arg == '--ignore':
                ai= getarg( ai, argv, options, 'ignore' )
            elif arg == '--ext':
                if ai+1 < acount:
                    ai+= 1
                    options['ext'].add( argv[ai].lower() )
                    options['use_ext']= True
            elif arg == '--copy_single':
                options['cmd']= 'f_copy_single'
            elif arg == '--copy':
                options['cmd']= 'f_copy'
        else:
            usage()
        ai+= 1

    if options['src'] and options['dest'] and options['cmd']:
        with ParallelCopy( options ) as copy:
            try:
                func= getattr( copy, options['cmd'] )
            except AttributeError:
                usage()
            func()
    else:
        usage()

    return  0


if __name__=='__main__':
    sys.exit( main( sys.argv ) )



