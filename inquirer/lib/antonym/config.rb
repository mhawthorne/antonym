require 'yaml'

module Antonym

  class Configuration

    # returns:
    #   Configuration instance
    def self.from_path(path)
      open(path) do |stream|
        Configuration.from_stream(stream)
      end
    end
    
    # returns:
    #   Configuration instance
    def self.from_stream(stream)
      config_hash = YAML.load(stream)
      
      raise Exception("malformed yaml in #{config_path}") unless config_hash.respond_to?(:has_key?)
      
      find_config = lambda do |key|
        raise Exception.new("#{key} required in config") unless config_hash.has_key?(key)
        config_hash[key]
      end
      
      raw_url = find_config.call("app_url")
      app_name = find_config.call("app_name")
      user = find_config.call("user")
      passwd = find_config.call("password")
      admin = config_hash.has_key?("admin")
      app_service_prefix = find_config.call("app_service_prefix")
      Configuration.new(app_name, URI.parse(raw_url), app_service_prefix, user, passwd, admin)
    end
    
    attr_reader :app_name, :app_uri, :app_service_prefix, :user, :password, :admin
    
    def initialize(app_name, app_uri, app_service_prefix, user, password, admin)
      @app_name = app_name
      @app_uri = app_uri
      @app_service_prefix = app_service_prefix
      @user = user
      @password = password
      @admin = admin
    end
    
  end
  
end