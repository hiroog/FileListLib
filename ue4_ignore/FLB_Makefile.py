# 2018 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

sys.path.append( os.path.join( tool.getEnv( 'UALIB', tool.getEnv( 'FLATLIB' ) ), '../FileListLib' ) )


BACKUP_DIR= '../backup_engine'
RELEASE_DIR= '../copy_engine'

GREP_PATTERN= r'PATTERN'


#------------------------------------------------------------------------------

def func_nop( task ):
    pass

tool.addScriptTask( genv, 'build', func_nop )

#------------------------------------------------------------------------------

def func_copy( task ):
    import FileTools
    ignorefile= '.fl_ue4_' + task.ignorefile
    cmd= [ '', '-i',  ignorefile, '--copy', task.dest_dir ]
    FileTools.main( cmd )

task= tool.addScriptTask( genv, 'copy_backup', func_copy )
task.ignorefile= 'backup'
task.dest_dir= BACKUP_DIR

task= tool.addScriptTask( genv, 'copy_release', func_copy )
task.ignorefile= 'copy'
task.dest_dir= RELEASE_DIR

#------------------------------------------------------------------------------

def func_list( task ):
    import FileTools
    ignorefile= '.fl_ue4_' + task.ignorefile
    cmd= [ '', '-i',  ignorefile, '--list' ]
    FileTools.main( cmd )

task= tool.addScriptTask( genv, 'list_backup', func_list )
task.ignorefile= 'backup'

task= tool.addScriptTask( genv, 'list_release', func_list )
task.ignorefile= 'copy'

#------------------------------------------------------------------------------

def func_grep( task ):
    import FileTools
    ignorefile= '.fl_ue4_' + task.ignorefile
    cmd= [ '', '-i',  ignorefile, '--grep', task.pattern ]
    FileTools.main( cmd )

task= tool.addScriptTask( genv, 'grep', func_grep )
task.ignorefile= 'grep'
task.pattern= GREP_PATTERN


#------------------------------------------------------------------------------




