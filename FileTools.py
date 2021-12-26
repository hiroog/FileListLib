# 2018/01/14 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

import  os, stat
import  sys
import  re
import  time
import  shutil

sys.path.append( os.path.dirname( sys.argv[0] ) )
import  FileListLib

class LogOutput:
    def __init__( self ):
        self.Verbose= False
        self.LogFile= None
    def open_log( self, file_name ):
        self.LogFile= open( file_name, 'w' )
    def p( self, *args ):
        print( *args )
        if self.LogFile:
            for arg in args:
                self.LogFile.write( str(arg) )
                self.LogFile.write( ' ' )
            self.LogFile.write( '\n' )
    def v( self, *args ):
        if self.Verbose:
            self.p( *args )
    def wb( self, arg ):
        sys.stdout.flush()
        sys.stdout.buffer.write( arg )
        if self.LogFile:
            self.LogFile.flush()
            self.LogFile.buffer.write( arg )

Log= LogOutput()

#------------------------------------------------------------------------------

class UTF8Tools2:
    def __init__( self ):
        pass

    def convert( self, file_name, output_name, en_src, en_dest ):
        with open( file_name, 'r', encoding=en_src ) as fi:
            with open( output_name, 'w', encoding=en_dest ) as fo:
                fo.write( fi.read() )

    def isUTF8( self, file_name ):
        try:
            with open( file_name, 'r', encoding='utf-8', errors='strict' ) as fi:
                fi.read()
        except UnicodeError:
            return  False
        return  True

    def isSJIS( self, file_name ):
        try:
            with open( file_name, 'r', encoding='cp932', errors='strict' ) as fi:
                fi.read()
        except UnicodeError:
            return  False
        return  True


#------------------------------------------------------------------------------

class FileTools:
    def __init__( self ):
        pass

    def f_copy_target( self, file_list, options ):
        base_dir= options['base']
        target= options['target']
        force_copy= options['force']
        verbose= options['verbose']
        Log.p( 'copy %s to %s' % (base_dir,target) )
        start= time.perf_counter()
        total_count= len(file_list)
        copy_index= 0
        file_count= 0
        base_offset= len(base_dir)
        progress_step= 1.0/10
        progress= progress_step
        for file_name in file_list:
            skip= False
            path= file_name[base_offset:]
            if path[0] == '/':
                path= path[1:]
            dest_file= os.path.join( target, path )
            dir= os.path.dirname( dest_file )
            if not os.path.exists( dir ):
                os.makedirs( dir )
            elif not force_copy:
                if os.path.exists( dest_file ):
                    src_time= os.path.getmtime( file_name )
                    dest_time= os.path.getmtime( dest_file )
                    if src_time <= dest_time:
                        skip= True
            if not skip:
                if verbose:
                    Log.v( file_name + ' --> ' + dest_file )
                shutil.copy( file_name, dest_file )
                file_stat= os.stat( dest_file )
                os.chmod( dest_file, file_stat.st_mode | stat.S_IWRITE )
                file_count+= 1
            copy_index+= 1
            if copy_index / total_count > progress:
                sec= time.perf_counter() - start
                Log.p( " %d%%  %.2f sec" % (progress * 100,sec) )
                progress+= progress_step
        Log.p( 'copy %d files' % file_count )
        return  file_list

    def f_grep( self, file_list, options ):
        pattern= options['pattern']
        verbose= options['verbose']
        grep_pat= re.compile( pattern.encode( encoding='utf-8' ) )
        grep_list= []
        for file_name in file_list:
            with open( file_name, 'rb' ) as fi:
                line_num= 0
                added_flag= False
                for line in fi:
                    line_num+= 1
                    pat= grep_pat.search( line )
                    if pat is not None:
                        if not added_flag:
                            grep_list.append( file_name )
                            added_flag= True
                        if verbose:
                            Log.v( '[%s] %d' % (file_name, line_num) )
                            Log.wb( line )
                            Log.wb( b'\r\n' )
                        else:
                            Log.p( file_name )
                            break
        return  grep_list

    def f_noutf8( self, file_list, options ):
        u8tools= UTF8Tools2()
        c_cp932= 0
        c_utf8= 0
        c_unknown= 0
        grep_list= []
        for file_name in file_list:
            if u8tools.isUTF8( file_name ):
                c_utf8+= 1
            elif u8tools.isSJIS( file_name ):
                c_cp932+= 1
                grep_list.append( file_name )
            else:
                c_unknown+= 1
                grep_list.append( file_name )
        Log.p( '# utf8', c_utf8 )
        Log.p( '# cp932', c_cp932 )
        Log.p( '# erros', c_unknown )
        return  grep_list

    def f_cvutf8( self, file_list, options ):
        u8tools= UTF8Tools2()
        for file_name in file_list:
            if u8tools.isSJIS( file_name ):
                src_temp= file_name + '.cp932.src'
                if not os.path.exists( src_temp ):
                    os.rename( file_name, src_temp )
                output_name= file_name
                Log.v( src_temp, '-->', output_name )
                u8tools.convert( src_temp, output_name, 'cp932', 'utf-8' )
        return  file_list

    def f_size_command( self, file_list, options ):
        total= 0
        for file_name in file_list:
            total+= os.path.getsize( file_name )
        #Log.p( 'size= %d byte' % total )
        mark= "GMK"
        unit= 1024*1024*1024
        index= 0
        while unit >= 1024:
            if total >= unit:
                Log.p( 'size= %.2f %c  (%d byte)' % (total/unit,mark[index],total) )
                break
            index+= 1
            unit>>= 10
        return  file_list

    def f_file_list( self, file_list, options ):
        for file_name in file_list:
            Log.p( file_name )
        return  file_list

    def f_save_list( self, file_list, options ):
        save_file= options['save']
        with open( save_file, 'w', encoding='utf-8' ) as fo:
            for file_name in file_list:
                fo.write( '%s\n' % file_name )
            fo.write( '# %d\n' % len(file_list) )
        Log.p( 'save: %d %s' % (len(file_list), save_file) )
        return  file_list

    def f_load_list( self, file_list, options ):
        load_file= options['load']
        load_list= []
        with open( load_file, 'r', encoding='utf-8' ) as fi:
            for line in fi:
                name= line.strip()
                if name == '' or name[0] == '#':
                    continue
                load_list.append( name )
        Log.p( 'load: %d %s' % (len(load_list), load_file) )
        file_list.extend( load_list )
        return  file_list

    def f_difftree( self, file_list, options ):
        diffroot= options['diffroot']
        diff_list= []
        for file_name in file_list:
            target_path= os.path.join( diffroot, file_name )
            if not os.path.exists( target_path ):
                diff_list.append( file_name )
                Log.v( target_path )
        return  diff_list

    def f_pathmatch( self, file_list, options ):
        match_pat= re.compile( options['pathmatch'] )
        diff_list= []
        for file_name in file_list:
            pat= match_pat.search( file_name )
            if pat is not None:
                diff_list.append( file_name )
        return  diff_list

    def f_pathstrip( self, file_list, options ):
        match_pat= re.compile( options['pathstrip'] )
        diff_list= []
        for file_name in file_list:
            pat= match_pat.search( file_name )
            if pat is not None:
                diff_list.append( pat.group(1) )
        return  diff_list

    def f_ignore( self, file_list, options ):
        ignore_file= options['ignore']
        fll= FileListLib.FileListLib( ignore_file )
        file_list= fll.find_file( options['base'] )
        return  file_list

    def f_findtree( self, file_list, options ):
        ignore_file= options['ignore']
        fll= FileListLib.FileListLib()
        file_list= fll.find_file_preload( options['base'], ignore_file )
        return  file_list

    def f_dir( self, file_list, options ):
        sfile= set()
        for file_name in file_list:
            root,name= os.path.split( file_name )
            sfile.add( root )
        return  list( sfile )

    def f_unique( self, file_list, options ):
        sfile= set()
        for file_name in file_list:
            sfile.add( file_name )
        return  list( sfile )

    def f_setwritable( self, file_list, options ):
        sfile= set()
        for file_name in file_list:
            file_stat= os.stat( file_name )
            os.chmod( file_name, file_stat.st_mode | stat.S_IWRITE )
        return  file_list

    def f_clear( self, file_list, options ):
        return  []


#------------------------------------------------------------------------------

def usage():
    print( 'FileTools.py v1.35 2020/10/11 Hiroyuki Ogasawara' )
    print( 'usage: FileTools.py [<options|commands>] [<base_dir>]' )
    print( 'command:' )
    print( '  -i,--ignore <ignore_file>' )
    print( '  -ig' )
    print( '  --findtree <ignore_file>' )
    print( '  --copy <target_folder>' )
    print( '  -l,--list' )
    print( '  --size' )
    print( '  --grep <pattern>' )
    print( '  --load <file_name>' )
    print( '  --save <file_name>' )
    print( '  --difftree <diff_root>' )
    print( '  --pathmatch <pattern>' )
    print( '  --pathstrip <pattern>' )
    print( '  --dir' )
    print( '  --unique' )
    print( '  --noutf8' )
    print( '  --cvutf8' )
    print( '  --setwritable' )
    print( '  --clear' )
    print( 'option:' )
    print( '  --force                    force overwrite' )
    print( '  --clog <file_name>         output console log' )
    print( '  -v,--verbose' )
    print( 'ex. FileTools.py -i .flignore src --copy dest' )
    sys.exit( 1 )

def getArg( ai, argv, options, opt_name ):
    if ai+1 < len(argv):
        ai+= 1
        options[opt_name]= argv[ai]
    return  ai


def main( argv ):
    options= {
        'base' : '.',
        'force' : False,
        'target': None,
        'verbose': False,
        'ignore': '.flignore',
    }
    action_list= []

    acount= len(argv)
    ai= 1
    while ai < acount:
        arg= argv[ai]
        if arg[0] == '-':
            if arg == '--debug':
                FileListLib.Log.DebugOutput= True
            elif arg == '-i' or arg == '--ignore':
                if ai+1 < acount:
                    ai+= 1
                    options['ignore']= argv[ai]
                    action_list.append( 'f_ignore' )
            elif arg == '--findtree':
                if ai+1 < acount:
                    ai+= 1
                    options['ignore']= argv[ai]
                    action_list.append( 'f_findtree' )
            elif arg == '--copy':
                if ai+1 < acount:
                    ai+= 1
                    options['target']= argv[ai]
                    action_list.append( 'f_copy_target' )
            elif arg == '--grep':
                if ai+1 < acount:
                    ai+= 1
                    options['pattern']= argv[ai]
                    action_list.append( 'f_grep' )
            elif arg == '--save':
                if ai+1 < acount:
                    ai+= 1
                    options['save']= argv[ai]
                    action_list.append( 'f_save_list' )
            elif arg == '--load':
                if ai+1 < acount:
                    ai+= 1
                    options['load']= argv[ai]
                    action_list.append( 'f_load_list' )
            elif arg == '--difftree':
                if ai+1 < acount:
                    ai+= 1
                    options['diffroot']= argv[ai]
                    action_list.append( 'f_difftree' )
            elif arg == '--pathmatch':
                if ai+1 < acount:
                    ai+= 1
                    options['pathmatch']= argv[ai]
                    action_list.append( 'f_pathmatch' )
            elif arg == '--pathstrip':
                if ai+1 < acount:
                    ai+= 1
                    options['pathstrip']= argv[ai]
                    action_list.append( 'f_pathstrip' )
            elif arg == '-ig':
                action_list.append( 'f_ignore' )
            elif arg == '--size':
                action_list.append( 'f_size_command' )
            elif arg == '--dir':
                action_list.append( 'f_dir' )
            elif arg == '--unique':
                action_list.append( 'f_unique' )
            elif arg == '--clear':
                action_list.append( 'f_clear' )
            elif arg == '-l' or arg == '--list':
                action_list.append( 'f_file_list' )
            elif arg == '--noutf8':
                action_list.append( 'f_noutf8' )
            elif arg == '--cvutf8':
                action_list.append( 'f_cvutf8' )
            elif arg == '--setwritable':
                action_list.append( 'f_setwritable' )
            elif arg == '--force':
                options['force']= True
            elif arg == '-v' or arg == '--verbose':
                options['verbose']= True
            elif arg == '--clog':
                if ai+1 < acount:
                    ai+= 1
                    Log.open_log( argv[ai] )
            else:
                usage()
        else:
            options['base']= arg
        ai+= 1

    Log.Verbose= options['verbose']
    if action_list != []:
        start= time.perf_counter()
        file_list= []

        ftool= FileTools()
        for action in action_list:
            Log.p( '#begin [%s] in %d files' % (action, len(file_list)) )
            try:
                func= getattr( ftool, action )
            except AttributeError:
                usage()
                break
            file_list= func( file_list, options )
            Log.p( '#end [%s] out %d files' % (action, len(file_list)) )
    else:
        usage()

    Log.v( '#total: %.2f sec' % (time.perf_counter() - start) )
    return  0


if __name__ == '__main__':
    sys.exit( main( sys.argv ) )



