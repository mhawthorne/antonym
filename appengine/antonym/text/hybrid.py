class HybridSpeaker:
    
    def __init__(self, *speakers):
        self.__speakers = speakers
        
    def ingest(self, phrase):
        for s in self.__speakers:
            s.ingest(phrase)

    def compile(self):
        for s in self.__speakers:
            s.compile()
        
    def speak(self, min_length, max_length):
        pass
        
