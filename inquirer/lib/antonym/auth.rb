require 'cgi'


module Antonym
  
  class AuthenticationException < StandardError
    
    def self.from_response(response)
      AuthenticationException.new("#{response.status}\n#{response.header.all.inspect}\n#{response.content}")
    end
    
  end


  module AuthHelper
  
    def self.urlencode_hash(hash)
      hash.collect { |k, v| "#{CGI.escape(k)}=#{CGI.escape(v)}" }.join("&")
    end
  
  end


  class Authenticator

    def initialize(app_uri, app_name)
      @app_uri = app_uri
      @app_name = app_name
      @is_localhost = (app_uri.host == "localhost")
    end
  
    def get_login_cookie(user, passwd, args={})
      client = HTTPClient.new
      login(user, passwd, client, args)
      client.cookie_manager.cookies
    end
  
    def login_client(user, passwd, client, args={})
      login(user, passwd, client, args)
    end
  
    private
  
      def login(user, passwd, client, args)
        if @is_localhost
          if args.fetch(:admin, false)
            admin = "True"
          else
            admin = "False"
          end
          login_cookies = local_login_cookies(user, admin)
          # puts "cookies: #{login_cookies}"
          client.cookie_manager.parse(login_cookies, @app_uri)
        else
          login_hash = google_login(user, passwd, @app_name, client)
          auth = login_hash.fetch("Auth", nil)
          raise AuthenticationException.new("no auth token returned in: #{login_hash.inspect}") if auth.nil?
          
          auth_hash = {"auth" => auth, "continue" => "#{@app_uri}/_/echo" }
          response = client.get("#{@app_uri}/_ah/login?#{AuthHelper.urlencode_hash(auth_hash)}")
          validate_response(response) { |response| response.status == 302 }
        end
      end
  
      def validate_response(response)
        if block_given?
          valid = yield response
        else
          valid = (response.status >= 200 or response.status <= 300)
        end
        raise AuthenticationException.from_response(response) unless valid
      end
    
      def google_login(user, passwd, app_name, client)
        login_hash = {}
        login_body = { "Email" => user,
          "Passwd" =>  passwd,
          "service" => "ah",
          "source" =>  app_name,
          "accountType" => "HOSTED_OR_GOOGLE" }
        response = client.post("https://www.google.com/accounts/ClientLogin", login_body)
        validate_response(response)
        response.content.split(/\n/).each do |line|
          k, v = line.split(/\=/)
          login_hash[k] = v
        end
        login_hash
      end
    
      def local_login_cookies(user, admin)
        # "dev_appserver_login=#{user}:#{admin}:185804764220139124118"
        "dev_appserver_login=#{user}:#{admin}:1"
      end
  
  end

end