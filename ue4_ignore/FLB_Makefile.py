# vim:ts=4 sw=4 et:

sys.path.append( os.path.join( tool.getEnv( 'UALIB', tool.getEnv( 'FLATLIB' ) ), '../FileListLib' ) )


def func_nop( task ):
    pass

tool.addScriptTask( genv, 'build', func_nop )


def func_copy( task ):
    import FileTools
    ignorefile= '.fl_ue4_' + task.ignorefile
    cmd= [ '', '-i',  ignorefile, '--copy', task.dest_dir ]
    FileTools.main( cmd )

task= tool.addScriptTask( genv, 'copy_backup', func_copy )
task.ignorefile= 'backup'
task.dest_dir= '../backup_engine'

task= tool.addScriptTask( genv, 'copy_release', func_copy )
task.ignorefile= 'copy'
task.dest_dir= '../copy_engine'


def func_list( task ):
    import FileTools
    ignorefile= '.fl_ue4_' + task.ignorefile
    cmd= [ '', '-i',  ignorefile, '--list' ]
    FileTools.main( cmd )

task= tool.addScriptTask( genv, 'list_backup', func_list )
task.ignorefile= 'backup'

task= tool.addScriptTask( genv, 'list_copy', func_list )
task.ignorefile= 'copy'

