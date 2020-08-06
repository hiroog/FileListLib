# 2018/01/14 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

import  os, stat
import  sys
import  time
import  shutil
import  FileListLib

class FileTools:
    def __init__( self ):
        pass

    def f_copy_target( self, file_list, options ):
        base_dir= options['base']
        target= options['target']
        force_copy= options['force']
        print( 'copy %s to %s' % (base_dir,target) )
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
                #print( file_name + ' ----> ' + dest_file )
                shutil.copy( file_name, dest_file )
                os.chmod( dest_file, stat.S_IWRITE )
                file_count+= 1
            copy_index+= 1
            if copy_index / total_count > progress:
                sec= time.perf_counter() - start
                print( " %d%%  %.2f sec" % (progress * 100,sec) )
                progress+= progress_step
        print( 'copy %d files' % file_count )

    def f_size_command( self, file_list, options ):
        total= 0
        for file_name in file_list:
            total+= os.path.getsize( file_name )
        #print( 'size= %d byte' % total )
        mark= "GMK"
        unit= 1024*1024*1024
        index= 0
        while unit >= 1024:
            if total >= unit:
                print( 'size= %.2f %c  (%d byte)' % (total/unit,mark[index],total) )
                break
            index+= 1
            unit>>= 10

    def f_file_list( self, file_list, options ):
        total= 0
        for file_name in file_list:
            print( file_name )

def usage():
    print( 'FileTools.py v1.10 2018/01/14 Hiroyuki Ogasawara' )
    print( 'usage: FileTools.py [options] <base_dir>' )
    print( '  --ignore <ignore_file>   (default .flignore)' )
    print( '  --copy <target_folder>' )
    print( '  -l,--list' )
    print( '  --size' )
    print( '  --force                  force overwrite' )
    print( '  --log                    output to output.log' )
    print( 'ex. FileTools.py src --copy dest' )
    sys.exit( 1 )


def main( argv ):
    options= {
        'base' : '.',
        'force' : False,
        'target': None,
    }
    action= None
    ignore_file= '.flignore'
    logging= False

    acount= len(argv)
    ai= 1
    while ai < acount:
        arg= argv[ai]
        if arg[0] == '-':
            if arg == '--debug':
                FileListLib.Log.DebugOutput= True
            elif arg == '--ignore':
                if ai+1 < acount:
                    ai+= 1
                    ignore_file= argv[ai]
            elif arg == '--force':
                options['force']= True
            elif arg == '--copy':
                if ai+1 < acount:
                    ai+= 1
                    options['target']= argv[ai]
                    action= 'f_copy_target'
                else:
                    action= None
            elif arg == '--size':
                action= 'f_size_command'
            elif arg == '-l' or arg == '--list':
                action= 'f_file_list'
            elif arg == '--log':
                logging= True
            else:
                usage()
        else:
            options['base']= arg
        ai+= 1

    if action:
        start= time.perf_counter()

        fll= FileListLib.FileListLib( ignore_file )
        file_list= fll.find_file( options['base'] )

        print( '#pass: %d files (%.2f sec)' % (len(file_list), time.perf_counter() - start) )

        if logging:
            with open( 'output.log', 'w', encoding='utf-8' ) as fo:
                fo.write( '=============\n' )
                for name in file_list:
                    fo.write( name + '\n' )
                fo.write( 'file=%d\n' % len(file_list) )

        ftool= FileTools()
        try:
            func= getattr( ftool, action )
            func( file_list, options )
        except AttributeError:
            usage()
    else:
        usage()

    print( '#total: %.2f sec' % (time.perf_counter() - start) )
    return  0


if __name__ == '__main__':
    sys.exit( main( sys.argv ) )



