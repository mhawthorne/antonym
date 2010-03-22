require 'cgi'

require 'rubygems'
require 'json'


module Antonym
  
  class ServiceException < StandardError
    
    attr_reader :code
    
    def initialize(code, msg)
      @code = code
      super(msg)
    end
    
  end


  module Service
    
    def verify_response(response)
      s = response.status
      raise ServiceException.new(s, "#{s} #{response.reason}") if s < 200 or s > 299
    end
    
    def authenticated_client(args={})
      client = HTTPClient.new
      type = args.fetch(:type, nil)
      if type.nil?
        type = :google
      end
      
      #puts "authenticated_client type #{type}"
      
      if type == :google
        auth = Antonym::Authenticator.new(@config.app_uri, @config.app_name)
        auth.login_client(@config.user, @config.password, client, :admin => @config.admin)
      else
        uri = args.fetch(:uri, nil)
        client.set_auth(uri, @config.user, @config.password)
      end
      
      client
    end
    
  end


  class MixtureService
  
    include Service
    
    def initialize(config, args={})
      @config = config
    end
  
    def get(args={})
      client = authenticated_client()
      svc_uri = svc_uri(args)
      response = client.get(svc_uri)
      verify_response(response)
      return JSON.parse(response.content)
    end
    
    private

      def svc_uri(args)
        source = args.fetch(:source, nil)
        puts "source: #{source.inspect}"
        raw = "#{@config.app_uri}/api/mixture"
        raw << "/#{source}" unless source.nil?
        URI.parse(raw)
      end
      
  end


  class ArtifactService
    
      include Service
    
      def initialize(config, args={})
        @config = config
        @listener = args.fetch(:listener, nil)
      end
  
      def get(guid)
        svc_uri = svc_uri(:guid => guid)
        response = new_bulk_client(:uri => svc_uri).get(svc_uri)
        verify_response(response)
        return JSON.parse(response.content)
      end
    
      def put(guid, artifact_hash)
        svc_uri = svc_uri(:guid => guid)
        response = new_bulk_client(:uri => svc_uri).put(svc_uri, artifact_hash.to_json())
        verify_response(response)
      end
      
      def post(artifact_hash)
        response = new_bulk_client(:uri => svc_uri).post(svc_uri, artifact_hash.to_json())
        verify_response(response)
      end
      
      def search(term)
        base_uri = svc_uri(:v => '')
        term = CGI.escape(term)
        uri = "#{base_uri}/-/search?q=#{term}"
        @listener.request(uri, 'GET')
        response = new_client().get(uri)
        verify_response(response)
        return JSON.parse(response.content)
      end
      
      private

        def new_bulk_client(args={})
          args.update(:type => :digest)
          authenticated_client(args)
        end
        
        def new_client(args={})
          args.update(:type => :google)
          authenticated_client(args)
        end
        
        def svc_uri(args={})
          # most services want artifacts2, except search
          v = args.fetch(:v, 2)
          # using "bulk" interface to avoid captchas
          raw = "#{@config.app_uri}/api/artifacts#{v}"
          guid = args.fetch(:guid, nil)
          raw << "/#{guid}" unless guid.nil?
          URI.parse(raw)
        end

  end


  class SourceService
    
      include Service
    
      def initialize(config, args={})
        @config = config
        @listener = args.fetch(:listener, nil)
      end
  
      def list()
        client = authenticated_client()
        uri = svc_uri()
        response = client.get(uri)
        verify_response(response)
        return JSON.parse(response.content)
      end
      
      def get(name)
        client = authenticated_client()
        uri = svc_uri(:name => name)
        response = client.get(uri)
        verify_response(response)
        return JSON.parse(response.content)
      end
      
      def delete(name)
        client = authenticated_client()
        uri = svc_uri(:name => name)
        response = client.delete(uri)
        verify_response(response)
      end
      
      private
      
        def svc_uri(args={})
          raw = "#{@config.app_uri}/api/sources"
          name = args.fetch(:name, nil)
          raw << "/#{name}" unless name.nil?
          URI.parse(raw)
        end
      
  end
  
  
  class DataAnalysisService
    
    include Service
    
    def initialize(config, args={})
      @config = config
      @listener = args.fetch(:listener, nil)
    end

    def get(kind)
        client = authenticated_client()
        uri = svc_uri(kind)
        response = client.get(uri)
        verify_response(response)
        return JSON.parse(response.content)
    end
    
    def delete(kind)
        client = authenticated_client()
        uri = svc_uri(kind)
        @listener.request(uri, 'DELETE')
        response = client.delete(uri)
        @listener.response(uri, response)
        verify_response(response)
        return JSON.parse(response.content)
    end
    
    private

        def svc_uri(kind)
          raw = "#{@config.app_uri}/api/da/kinds/#{kind}"
          URI.parse(raw)
        end

  end
  
  
  class TwitterService
    
    include Service
  
    def initialize(config, args={})
      @config = config
      @listener = args.fetch(:listener, nil)
    end

    def act
      client = authenticated_client()
      uri = svc_uri("act")
      @listener.request(uri, "POST")
      response = client.post(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end
    
    def direct(status)
      client = authenticated_client()
      uri = svc_uri("direct")
      @listener.request(uri, "POST")
      response = client.post(uri, status)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end
    
    def mix
      client = authenticated_client()
      uri = svc_uri("mix")
      @listener.request(uri, "POST")
      response = client.post(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end

    def state
      client = authenticated_client()
      uri = svc_uri("state")
      @listener.request(uri, "GET")
      response = client.get(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end

    private

      def svc_uri(action)
        raise ServiceException.new("action required") if action.nil?
        raw = "#{@config.app_uri}/api/twitter"
        raw << "/#{action}"
        URI.parse(raw)
      end
    
  end
  
  
  class CronService
    
    include Service
    
    def initialize(config, args={})
      @config = config
      @listener = args.fetch(:listener, nil)
    end

    def tweet_mix
      client = authenticated_client()
      uri = svc_uri("twitter/mix")
      @listener.request(uri, "GET")
      response = client.get(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end
    
    private

      def svc_uri(action)
        raise ServiceException.new("action required") if action.nil?
        raw = "#{@config.app_uri}/cron"
        raw << "/#{action}"
        URI.parse(raw)
      end
    
  end
  
end