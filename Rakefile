$default_host = "http://localhost:9009"
$appengine_dir = 'appengine'
$gae_home_default = "#{ENV['HOME']}/opt/google_appengine"

ADMIN_EMAIL = 'meh.subterfusion@gmail.com'
APPENGINE_DIR = 'appengine'
APP_ID = 'meh-antonym'
DATA_EXPORT_DIR = 'tmp/backup'
PASSWD_FILE = 'tmp/passwd'

$fileutils = FileUtils::Verbose

def flag_is_false(val)
  return val == "no"
end

def fail(msg, code=1)
  $stderr.puts "ERROR - #{msg}"
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
  puts "=> #{cmd}" unless not secure.empty?
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
      lib_basename = File.basename(lib)
      rm_path = "#{d}/#{lib_basename}"
      $fileutils.rm_r rm_path if File.exists?(rm_path)
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


def load_test_modules(test_dir, test_suffix)
  test_modules = []
  test_files = load_tests(test_dir, test_suffix)
  test_files.each do |test_file|
    test_module = test_file[test_dir.size+1..-4].gsub(/\//, ".")
    test_modules << test_module
  end
  test_modules
end

namespace :test do
  
  desc "runs unit tests"
  task :u => [:clean] do
    use_coverage = get_env("coverage", :no)
    open = get_env("open", :no)
    
    test_dir = "test/unit"
    cmd_prefix = "#{gae_python_path_string()}:#{test_lib()}:#{test_dir} && python2.5 "
    cmd_prefix << coverage_prefix() unless use_coverage == :no
    
    test_modules = load_test_modules(test_dir, "*_test.py")
    joined_test_modules = test_modules.join(" ")
    run "#{cmd_prefix} test/runner.py #{joined_test_modules}"
    unless use_coverage == :no
      run "coverage html"
      unless open == :no
        run "open htmlcov/index.html"
      end
    end
  end

  desc "runs integration tests"
  task :i => [:clean] do
    host = get_env("host", $default_host)
  
    test_dir = "test/integration"
    cmd_prefix = "export PYTHONPATH=#{$lib_dir}:#{test_lib()}:#{test_dir} && python2.5"
    
    # test_modules = load_test_modules(test_dir, "*_test.py")
    # joined_test_modules = test_modules.join(" ")
    # run "#{cmd_prefix} test/runner.py #{joined_test_modules} - #{host}"
    
    tests = load_tests(test_dir, "*_test.py")
    tests.each do |test|
      run "#{cmd_prefix} #{test} #{host}"
    end
  end

end

def coverage_prefix
  coverage_bin = `which coverage`.strip
  fail "coverage.py not found" if coverage_bin.empty?
  "#{coverage_bin} run --source=\"katapult,antonym\""
end

desc "runs appengine locally"
task :run_app => [ :lib_copy ] do
  port = get_env("port", 9009)
  args = get_env("args", "")
  coverage = get_env("coverage", :no)
  gserver = "#{locate_gae()}/dev_appserver.py"
  
  
  cmd = "/usr/bin/python2.5 "
  cmd << coverage_prefix unless coverage == :no
  cmd << "#{gserver} -p #{port} --show_mail_body #{args} #{$appengine_dir} 2>&1 | tee tmp/gae.log"
  run cmd
end


task :verify_passwd do
  if not File.exist?(PASSWD_FILE)
    fail "file #{PASSWD_FILE} does not exist.  it should contain your appengine admin password"
  end
end

def find_appcfg_bin
  bin = `which appcfg.py`.strip
  fail "could not find appcfg.py" if bin.empty?
  bin 
end

desc "deploys application to appengine"
task :deploy => [ :lib_copy ] do
  default_login = :y
  login = get_env("login", default_login)
  
  appcfg = find_appcfg_bin()
  
  fail "#{appcfg_bin} not found" if appcfg.empty?
  
  cmd = ""
  use_login = (login == default_login)
  if use_login
    Rake::Task["verify_passwd"].execute
    cmd << "cat #{PASSWD_FILE} | "
  end
  
  cmd << "python2.5 #{appcfg} "
  cmd << "--passin " if use_login  
  cmd << "--email=#{ADMIN_EMAIL} "
  cmd << "update #{$appengine_dir}"
  run cmd
end

desc "fetches HTTP logs from appengine"
task :fetch_logs do
  out = get_env("out", "tmp/antonym.log")
  appcfg = find_appcfg_bin()

  Rake::Task["verify_passwd"].execute
  cmd = "cat #{PASSWD_FILE} | "
  
  cmd << "#{appcfg} --passin --email=#{ADMIN_EMAIL} request_logs #{$appengine_dir} #{out}"
  
  run cmd
end

def tstamp
  Time.now.strftime("%Y-%m-%d")
end

def create_dated_export_dir
  tstamp = tstamp()
  dated_export_dir = "#{DATA_EXPORT_DIR}/#{tstamp}"
  $fileutils.mkdir_p dated_export_dir
  dated_export_dir
end

def default_bulkloader_cmd(host, kind, file)
  "--kind=#{kind} --db_filename=tmp/#{kind}-progress.sql3 --result_db_filename=tmp/#{kind}-result.sql3 --filename=#{file} " <<
  "--url=#{host}/remote_api --email=#{ADMIN_EMAIL} --application=#{APP_ID} --passin "
end


def build_dump_cmd(host, kind, dir, keywords={})
  file = "#{dir}/#{kind}.sql3"
  
  "cat #{PASSWD_FILE} | " <<
  "python2.5 #{locate_gae()}/bulkloader.py --dump " <<
  default_bulkloader_cmd(host, kind, file) <<
  "--num_threads=1 " <<
  "#{APPENGINE_DIR}"
end

def build_restore_cmd(host, kind, path, keywords={})
  "cat #{PASSWD_FILE} | "  <<
  "python2.5 #{locate_gae()}/bulkloader.py --restore " <<
  default_bulkloader_cmd(host, kind, path) <<
  "#{APPENGINE_DIR}"
end


desc "deletes all derived files"
task :clean do
  clean = get_env("clean", :yes)
  if flag_is_false(clean)
    puts "skipping clean"
    next
  end
  
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


backup_kinds = [ 'Configuration', 'Feed', 'TwitterResponse' ]


namespace :restore do

  desc "restores backup for specified kind"
  task :kind do
    host = get_env("host", $default_host)
    kind = get_env("kind")
    path = get_env("path")
    run build_restore_cmd(host, kind, path)
  end

end


namespace :backup do
  
  desc "perform all automated backup steps"
  task :full => [ :clean, :download, :s3 ] do
  end
  
  desc "backs up all data of specified kinds"
  task :download => [ :verify_passwd ] do
    host = get_env("host", $default_host)
    kind = get_env("kind", :default)
    
    dated_export_dir = create_dated_export_dir()

    kinds = []
    if kind != :default
      kinds << kind
    else
      kinds.concat(backup_kinds)
    end
    
    kinds.each do |k|
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
