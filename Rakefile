$default_host = "http://localhost:9009"
$appengine_dir = 'appengine'
$gae_home_default = "#{ENV['HOME']}/opt/google_appengine"

ADMIN_EMAIL = 'mhawthorne@gmail.com'
APPENGINE_DIR = 'appengine'
APP_ID = 'meh-antonym'
DATA_EXPORT_DIR = 'tmp/backup'
PASSWD_FILE = 'tmp/passwd'

$fileutils = FileUtils::Verbose


def fail(msg, code=1)
  $stderr.puts msg
  exit code
end

def get_env(name, default=nil)
  if ENV.has_key?(name)
    ENV[name]
  elsif default
    puts "using default #{name}=#{default}"
    default
  else
    fail "#{name} not provided"
  end
end

def run(cmd)
  # secure flag allows me to run commands with passwords in them safely
  # (especially when output is emailed via cron)
  secure = get_env("secure", "")
  puts cmd unless not secure.empty?
  system cmd
  fail "'#{cmd}' failed with status #{$?.exitstatus}" if $?.exitstatus != 0
end


def python_path_string
  "export PYTHONPATH=#{$appengine_dir}"
end

def gae_python_path_string
  gae = locate_gae()
  "#{python_path_string()}:#{gae}:#{gae}/lib/webob:#{gae}/lib/yaml/lib"
end

def locate_gae
  gae_home = get_env("gae_home", $gae_home_default)
  fail "gae_home must be provided" if gae_home.empty?
  fail "gae_home location '#{gae_home}' not found" unless File.exist?(gae_home)
  gae_home
end

def test_lib
  "test/lib"
end


$lib_destinations = [ "appengine" ]
$lib_dir = "lib"

def each_lib
  Dir.glob("#{$lib_dir}/*").each do |lib|
    yield lib
  end
end


task :pythonpath do
  puts "#{python_path_string()}:#{gae_python_path_string()}"
end


desc "copies library files"
task :lib_copy do
  each_lib() do |lib|
    $lib_destinations.each do |d|
      $fileutils.cp_r lib, d
    end
  end
end


# loads tests from argument or loads all from provided directory and glob.
def load_tests(test_dir, glob)
  test = get_env("test", "")
  if test.empty?
    tests = Dir.glob("#{test_dir}/**/#{glob}")
  else
    tests = [test]
  end
  tests
end


desc "interactive python shell with app classes loaded"
task :shell do
  cmd = "#{gae_python_path_string()} && python2.5"
  run cmd
end

desc "runs script with app classes loaded"
task :script do
  s = get_env("s")
  cmd = "#{gae_python_path_string()} && python2.5 #{s}"
  run cmd  
end


desc "runs all tests"
task :test => [:test_unit, :test_integration]


namespace :test do
  
  desc "runs unit tests"
  task :u => [:clean] do
    cmd_prefix = "#{gae_python_path_string()}:#{test_lib()}:test/unit && python2.5"
    tests = load_tests("test/unit", "*_test.py")
    tests.each do |test|
      run "#{cmd_prefix} #{test} -v"
    end
  end

  desc "runs integration tests"
  task :i => [:clean] do
    host = get_env("host", $default_host)
  
    cmd_prefix = "export PYTHONPATH=#{$lib_dir}:#{test_lib()} && python2.5"
    tests = load_tests("test/integration", "*_test.py")
    tests.each do |test|
      run "#{cmd_prefix} #{test} #{host} -v"
    end
  end

end

desc "runs appengine locally"
task :run_app => [ :lib_copy ] do
  port = get_env("port", 9009)
  args = get_env("args", "")
  coverage = get_env("coverage", :no)
  gserver = "#{locate_gae()}/dev_appserver.py"
  coverage_bin = `which coverage`.strip
  
  cmd = "/usr/bin/python2.5 "
  # puts "coverage: #{coverage}"
  cmd << "#{coverage_bin} run " if coverage != :no
  cmd << "#{gserver} -p #{port} --show_mail_body #{args} #{$appengine_dir} 2>&1 | tee tmp/gae.log"
  run cmd
end


task :verify_passwd do
  if not File.exist?(PASSWD_FILE)
    fail "file #{PASSWD_FILE} does not exist.  it should contain your appengine admin password"
  end
end

desc "deploys application to appengine"
task :deploy => [ :lib_copy ] do
  default_login = "not-provided"
  login = get_env("login", default_login)
  
  appcfg_bin = "appcfg.py"
  appcfg = `which #{appcfg_bin}`.strip
  
  fail "#{appcfg_bin} not found" if appcfg.empty?
  
  cmd = ""
  use_login = (login != default_login)
  if use_login
    Rake::Task["verify_passwd"].execute
    passwd = get_passwd()
    cmd << "echo #{passwd} | "
  end
  
  cmd << "python2.5 #{appcfg} "
  cmd << "--passin " if use_login
  cmd << "update #{$appengine_dir}"
  run cmd
end


def create_dated_export_dir
  tstamp = Time.now.strftime("%Y-%m-%d")
  dated_export_dir = "#{DATA_EXPORT_DIR}/#{tstamp}"
  $fileutils.mkdir_p dated_export_dir
  dated_export_dir
end

def build_dump_cmd(host, kind, dir, keywords={})
  file = "#{dir}/#{kind}.sql3"
  
  "cat #{PASSWD_FILE} | " <<
  "python2.5 #{locate_gae()}/bulkloader.py --dump --kind=#{kind} --filename=#{file} " <<
  "--url=#{host}/remote_api --email=#{ADMIN_EMAIL} --app_id=#{APP_ID} --passin " <<
  "--num_threads=1 " <<
  "#{APPENGINE_DIR}"
end

def build_restore_cmd(host, kind, dir, keywords={})
  file = "#{dir}/#{kind}.sql3"

  "cat #{PASSWD_FILE} | "  <<
  "python2.5 #{locate_gae()}/bulkloader.py --restore --kind=#{kind} --filename=#{file} " <<
  "--url=#{host}/remote_api --email=#{ADMIN_EMAIL} --app_id=#{APP_ID} --passin " <<
  "#{APPENGINE_DIR}"
end


desc "deletes all derived files"
task :clean do
  [ 'appengine', 'lib', 'test' ].each do |d|
    glob = "#{d}/**/*.pyc"
    puts "cleaning #{glob}"
    FileList.new(glob).to_a.each do |pyc|
      $fileutils.rm pyc
    end
    puts
  end
end


namespace :svn do
  
  task :up do
    sh "svn up"
  end
  
end


backup_kinds = [ 'TwitterResponse' ]


namespace :restore do

  task :kind do
  end

end


namespace :backup do
  
  desc "perform all automated backup steps"
  task :full => [ :clean, :download, :s3 ] do
  end
  
  desc "backs up all data of specified kinds"
  task :download => [ :verify_passwd ] do
    host = get_env("host", $default_host)
    
    dated_export_dir = create_dated_export_dir()

    backup_kinds.each do |k|
      run build_dump_cmd(host, k, dated_export_dir)
    end
  end
  
  desc "pushes data backups to S3"
  task :s3 do
    run "s3sync.rb -v -r --progress --delete #{DATA_EXPORT_DIR}/ meh-antonym-backups:"  
  end
  
  desc "cleans local backups"
  task :clean do
    keep_count = get_env("keep", 30).to_i
    count = 0
    Dir.glob("#{DATA_EXPORT_DIR}/*").sort.reverse.each do |backup|
      count = count.next
      $stdout.write "#{count} #{backup} ... "
      if count <= keep_count
        puts "keep"
      else
        puts "delete"
        $fileutils.rm_r backup
      end
    end
  end
  
end
