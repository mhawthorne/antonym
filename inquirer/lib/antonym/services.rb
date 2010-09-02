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
      HttpClientFactory.new_client(@config, args)
    end
    
    def build_service_uri(path)
      "#{@config.app_uri}#{@config.app_service_prefix}#{path}"
    end
    
  end


  class HttpClientFactory
    
    def self.new_client(config, args={})
      client = HTTPClient.new
      type = args.fetch(:type, nil)
      if type.nil?
        type = :google
      end
      
      if type == :google
        auth = Antonym::Authenticator.new(config.app_uri, config.app_name)
        auth.login_client(config.user, config.password, client, :admin => config.admin)
      else
        uri = args.fetch(:uri, nil)
        client.set_auth(uri, config.user, config.password)
      end
      
      DelegatingHttpClient.new(client, args)
    end
    
  end
  
  
  class DelegatingHttpClient
    
    def initialize(source_client, kw={})
      @source_client = source_client
      @listener = kw.fetch(:listener, nil)
    end
    
    [ :delete, :head, :get, :post, :put ].each do |m|
      class_eval %{
          def #{m}(*args)
            # puts "args: \#\{args.inspect\}"
            http_method = "#{m.to_s.upcase}"
            uri = args[0]
            if args.size > 2
              headers = args[2]
            else
              headers = {}
            end
            # puts "\#\{http_method\} \#\{uri\}\n\#\{headers.inspect\}"
            @listener.request(uri, http_method, headers) unless @listener.nil?
            response = @source_client.send(:#{m}, *args)
            @listener.response(uri, response) unless @listener.nil?
            response
          end
      }
    end
    
  end
  
  
  class GenericService 
  
    include Service
  
    def initialize(config)
      @config = config
    end

    def delete(path, kw={})
      client = authenticated_client(:listener => ServiceListener.new )
      uri = "#{@config.app_uri}#{path}"
      response = client.delete(uri)
      verify_response(response)
      response
    end
  
    def get(path, kw={})
      client = authenticated_client(:listener => ServiceListener.new )
      uri = "#{@config.app_uri}#{path}"
      response = client.get(uri)
      verify_response(response)
      response
    end
  
    def put(path, kw={})
      body = kw[:body]
      client = authenticated_client(:listener => ServiceListener.new )
      uri = "#{@config.app_uri}#{path}"
      response = client.put(uri, body, build_headers(kw))
      verify_response(response)
      response
    end

    def post(path, kw={})
      body = kw[:body]
      client = authenticated_client(:listener => ServiceListener.new )
      uri = "#{@config.app_uri}#{path}"
      response = client.post(uri, body, build_headers(kw))
      verify_response(response)
      response
    end
  
    private
    
      def build_headers(kw)
        headers = {}
        if kw[:body].nil?
          headers['Content-Length'] = 0
        end
        headers
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
        raw = self.build_service_uri("/mixture")
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
        puts "ArtifactService.post artifact_hash: #{artifact_hash.inspect}"
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
          raw = self.build_service_uri("/artifacts")
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
          raw = self.build_service_uri("/sources")
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
          raw = self.build_service_uri("/da/kinds/#{kind}")
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

    def connections
      client = authenticated_client()
      uri = svc_uri("connections")
      @listener.request(uri, "GET")
      response = client.get(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end

    def messages
      client = authenticated_client()
      uri = svc_uri("messages")
      @listener.request(uri, "GET")
      response = client.get(uri)
      @listener.response(uri, response) unless @listener.nil?
      verify_response(response)
    end

    private

      def svc_uri(action)
        raise ServiceException.new("action required") if action.nil?
        raw = self.build_service_uri("/twitter")
        raw << "/#{action}"
        URI.parse(raw)
      end
    
  end


  class FeedService
    
    include Service
  
    def initialize(config, args={})
      @config = config
      @client = authenticated_client(args)
    end

    def get(source)
      return @client.get(svc_uri(:source => source))
    end
    
    def put(source, feed_hash)
      return @client.put(svc_uri(:source => source), feed_hash.to_json())
    end
    
    private

      def svc_uri(args={})
        source = args.fetch(:source, nil)
        raw = self.build_service_uri("/feeds")
        raw << "/#{source}" unless source.nil?
        URI.parse(raw)
      end
  end
  
end