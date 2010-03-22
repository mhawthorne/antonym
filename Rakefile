$default_host = "http://localhost:9009"
$appengine_dir = 'appengine'
$gae_home_default = "#{ENV['HOME']}/local/opt/google_appengine"

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
  script = get_env("script")
  cmd = "#{gae_python_path_string()} && python2.5 #{script}"
  run cmd  
end


desc "runs all tests"
task :test => [:test_unit, :test_integration]


desc "runs unit tests"
task :test_unit do
  cmd_prefix = "#{gae_python_path_string()}:#{test_lib()} && python2.5"
  tests = load_tests("test/unit", "*_test.py")
  tests.each do |test|
    run "#{cmd_prefix} #{test} -v"
  end
end

desc "runs integration tests"
task :test_integration do
  host = get_env("host", $default_host)
  
  cmd_prefix = "export PYTHONPATH=#{$lib_dir}:#{test_lib()} && python2.5"
  tests = load_tests("test/integration", "*_test.py")
  tests.each do |test|
    run "#{cmd_prefix} #{test} #{host} -v"
  end
end


desc "runs appengine locally"
task :run_app => [ :lib_copy ] do
  port = get_env("port", 9009)
  args=get_env("args", "")
  gserver = "#{locate_gae()}/dev_appserver.py"
  coverage = `which coverage`.strip
  run "/usr/bin/python2.5 #{coverage} run #{gserver} -p #{port} --show_mail_body #{args} #{$appengine_dir} 2>&1 | tee tmp/gae.log"
end


task :verify_passwd do
  if not File.exist?($passwd_file)
    fail "file #{$passwd_file} does not exist.  it should contain your appenngine admin password"
  end
end

desc "deploys application to appengine"
task :deploy => [ :lib_copy ] do
  default_login = "not-provided"
  login = get_env("login", default_login)
  
  appcfg = `which appcfg.py`.strip
  
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


desc "tests markov chain on input file"
task :speak do
  file = get_env("file")
  run "#{python_path_string()} && python2.5 #{$appengine_dir}/antonym/markov.py #{file}"
end