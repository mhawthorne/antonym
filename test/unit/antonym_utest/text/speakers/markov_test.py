from unittest import main, TestCase

from katapult.core import KeyCounter

from antonym.core import DataException
from antonym.text.speakers.markov import Markov2Speaker


_text = """Operation Tractable was the final offensive conducted by Canadian Army and Polish Army troops as part of the Battle of Normandy. The goal of this operation was to capture the strategically important
French town of Falaise, and following that, the smaller towns of Trun and Chambois. This operation was undertaken by the Polish 1st Armoured Division and the First Canadian Army against the
Wehrmacht's Army Group B, and it was a part of the largest encirclement on the German Western Front during World War II. Despite a slow start to the offensive that was marked by limited gains north of
Falaise, innovative tactics by Polish 1st Armoured Division, under the command of Stanislaw Maczek during the drive for Chambois enabled the Falaise Gap to be partially closed by August 19, 1944,
trapping about 150,000 German soldiers in the Falaise Pocket."""


def _log(msg):
    print msg


class Markov2Test(TestCase):
            
    def test_ingest_too_short(self):
        speaker = self.__new_speaker()
        self.assertRaises(DataException, self.__ingest_and_speak, speaker, "hi", 0, 130)
    
    def test_ingest_correct_length(self):
        speaker = self.__new_speaker()
        speaker.ingest(_text)
        speaker.compile()

        run_count = 100
        min_length = 70
        max_length = 130
        errors = KeyCounter()
        for i in xrange(run_count):
            try:
                result = speaker.speak(min_length, max_length)
                if len(result) < min_length:
                    errors.increment("short")
                elif len(result) > max_length:
                    errors.increment("long")
            except Exception, e:
                errors.increment(e)

        failures = []
        for k, v in errors.iteritems():
            # fails if error occurs more than 1% of the time
            if v > run_count * .01:
                failures.append((k, v))
        
        if failures:
            self.fail(failures)
            # print failures
        
    def __new_speaker(self):
        return Markov2Speaker()
        
    def __ingest_and_speak(self, speaker, ingest, min_length, max_length):
        # _log("ingesting %s" % ingest)
        speaker.ingest(ingest)
        speaker.compile()
        result = speaker.speak(min_length, max_length)
        # _log("speak(%d,%d): %s" % (min_length, max_length, result))
        return result
        
if __name__ == "__main__":
    main()