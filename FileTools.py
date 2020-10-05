# 2018/01/14 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

import  os, stat
import  sys
import  re
import  time
import  shutil
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

class UTF8Tools:
    ASCII= 0
    UTF8= 1
    CP932= 2
    ERROR= 3
    def __init__( self ):
        import  chardet
        self.chardet= chardet

    def convert( self, file_name, output_name, en_src, en_dest ):
        with open( file_name, 'r', encoding=en_src ) as fi:
            with open( output_name, 'w', encoding=en_dest ) as fo:
                fo.write( fi.read() )

    def isUTF8( self, file_name ):
        with open( file_name, 'rb' ) as fi:
            result= self.chardet.detect( fi.read() )
            encode= result['encoding']
            if encode == 'utf-8':
                return  UTF8Tools.UTF8
            if encode == 'ascii':
                return  UTF8Tools.ASCII
            if encode == 'SHIFT_JIS' or encode == 'CP932':
                return  UTF8Tools.CP932
        return  UTF8Tools.ERROR


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
                os.chmod( dest_file, stat.S_IWRITE )
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
        u8tools= UTF8Tools()
        grep_list= []
        for file_name in file_list:
            if u8tools.isUTF8( file_name ) == UTF8Tools.CP932:
                grep_list.append( file_name )
        return  grep_list

    def f_cvutf8( self, file_list, options ):
        u8tools= UTF8Tools()
        grep_list= []
        for file_name in file_list:
            if u8tools.isUTF8( file_name ) == UTF8Tools.CP932:
                grep_list.append( file_name )
                output_name= file_name + '.cvt_u8.txt'
                Log.p( file_name, '-->', output_name )
                u8tools.convert( file_name, output_name, 'cp932', 'utf-8' )
        return  grep_list

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
        total= 0
        for file_name in file_list:
            Log.p( file_name )
        return  file_list

#------------------------------------------------------------------------------

def usage():
    print( 'FileTools.py v1.20 2020/10/04 Hiroyuki Ogasawara' )
    print( 'usage: FileTools.py [options] <base_dir>' )
    print( '  -i,--ignore <ignore_file>  (default .flignore)' )
    print( '  --copy <target_folder>' )
    print( '  -l,--list' )
    print( '  --size' )
    print( '  --grep <pattern>' )
    print( '  --noutf8' )
    print( '  --force                    force overwrite' )
    print( '  --log                      output to output.log' )
    print( '  --clog <file_name>         output console log' )
    print( '  -v,--verbose' )
    print( 'ex. FileTools.py src --copy dest' )
    sys.exit( 1 )


def main( argv ):
    options= {
        'base' : '.',
        'force' : False,
        'target': None,
        'verbose': False,
    }
    action_list= []
    ignore_file= '.flignore'
    logging= False

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
                    ignore_file= argv[ai]
            elif arg == '--force':
                options['force']= True
            elif arg == '-v' or arg == '--verbose':
                options['verbose']= True
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
            elif arg == '--size':
                action_list.append( 'f_size_command' )
            elif arg == '-l' or arg == '--list':
                action_list.append( 'f_file_list' )
            elif arg == '--noutf8':
                action_list.append( 'f_noutf8' )
            elif arg == '--cvutf8':
                action_list.append( 'f_cvutf8' )
            elif arg == '--log':
                logging= True
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

        fll= FileListLib.FileListLib( ignore_file )
        file_list= fll.find_file( options['base'] )

        Log.v( '#pass: %d files (%.2f sec)' % (len(file_list), time.perf_counter() - start) )

        if logging:
            with open( 'output.log', 'w', encoding='utf-8' ) as fo:
                fo.write( '=============\n' )
                for name in file_list:
                    fo.write( name + '\n' )
                fo.write( 'file=%d\n' % len(file_list) )

        ftool= FileTools()
        for action in action_list:
            try:
                func= getattr( ftool, action )
                file_list= func( file_list, options )
            except AttributeError:
                usage()
                break
            Log.p( '#pass: %d files (%s)' % (len(file_list), action) )
    else:
        usage()

    Log.v( '#total: %.2f sec' % (time.perf_counter() - start) )
    return  0


if __name__ == '__main__':
    sys.exit( main( sys.argv ) )



