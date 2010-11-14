from unittest import main, TestCase

from antonym.text.speakers import SentenceSpeaker


_text = u"""
You know this meeting. It's the meeting that when anyone hears the attendee list, they instantly know, "Oh, it's that meeting". Something is up: a product is at risk, a strategy is
being redefined, or a decision  of magnitude is being considered. Slide reviews are  conducted via email, rehearsals are performed, and demos are  fine-tuned. When the day arrives,
the room fills, nervous glances are exchanged, and it begins. Your practice pays off.  Expected questions appear and are quickly answered. The project is solid; perhaps there is no
need for that massive decision. We're in good shape, except Allison, the SVP, has a  question. Allison? "Has anyone talked to Roger's group about this? Can they support this load?
Shit. The Screw-Me  Scenario describes the amazing silence in  the room when everyone understands the  colossal gap that Allison's questions unexpectedly  illuminate. That's a good
article to read if you want to figure out how to react. The question I want to answer here is how in the hell does a SVP who isn't even a part of this project, who was invited as a
courtesy, and who  has never even see  the project proposal find  the biggest strategic gap  in our thinking after staring  at our slides for  13 minutes? She had  a Twinge. Twinge
Acquisition As a manager,  you manage both yourself and your  team, and the simple fact is  there will always be more of them  than of you. Unless you're the  guy managing a single
person (weird), you've got multiple folks with  all their varied work and quirky personalities to manage. Rookie managers approach  this situation with enviable gusto. They believe
their job is to be aware of and responsible for their team's every single thought and act.  I like to watch these freshman managers. I like to watch them sweat and scurry about the
building as they attempt to complete  this impossible task. It's not that I enjoy watching them  prepare to fail. In fact, as they zip by, I explicitly  warn them: "There is no way
you're doing it all. You need to trust and you need to delegate." But even with this  explanation most of these managers are back in my office in three weeks saying the same thing:
"I have no idea how you keep track of it all". I don't. In addition to trusting those  who work for you by delegating work that you may truly believe only you can do, management is
also the art of listening  to a spartan set of data, extracting the  truth, and trusting your Twinges. When you do  this well, you look like a magician, but  when you screw up, the
consequences can be far ranging and damage the  project as well as your reputation with those involved. How to Build a Twinge Before  I explain how this truth extraction and Twinge
construction can really screw things  up, let's first understand why these managers aren't listening  to me and why I'm ok with that. Remember, I'm  talking about engineers here. A
class of human being that derives professional joy  from the building of things -- specific things. Things they can sit back and stare at  -- look there! -- I built that thing. The
building of things scratches an essential itch for engineers. It's why they became engineers in the first place. When they were six, their Dad handed them two boards, a nail, and a
hammer and they started whacking. BLAM BLAM BLAM. Even with the nail awkwardly bent in  half, the wood was suddenly and magically bound together: a thing was built. At that moment,
this junior engineer's brain excreted a chemical that instantly convinced them of the disproportionate  value of this construction. This is the best wood thing in the world because
I built it. And then they  looked up from their creation and pleaded, "Dad, I really  need more nails". Dad handed them three more nails, showed them  where to hold the hammer, and
demonstrated how to hit the nail. More whacking.  BLAM BLAM BIFF. This time the nail wasn't bent, this time on the last hit the  nail slid effortlessly into the wood. This engineer
in training had now experienced two essential emotions: the joy of creation and  the satisfaction of learning while gaining experience, perfecting the craft. Engineers are wired to
learn how to build stuff well, and as  they continue to do that someone eventually thinks it's a good idea to promote them  to become managers. These new managers initially believe
the essential skills of building  that made them successful as engineers will apply to  the building of people, and they don't. It's their experience  that matters. Management is a
total career restart. One of the first lessons a new manager discovers, either through  trial and error or instruction, is that the approaches they used for building product aren't
going to work  when it comes to people. However,  this doesn't mean all of the  experience is suddenly irrelevant. In fact,  it's that experience that creates the  Twinge. A Day of
Stories As a manager,  think of your day as one  full of stories. All day, you're  hearing stories from different people about  the different arcs that are being  played out in the
hallways and conference rooms. As these stories arrive, there is one question you need to always be asking: do you believe this story? Before you make that call, there are a couple
things you need to know. First, this story is incomplete, and you're ok with that. Here's why: for now, you need to trust that those who work with you are capable of synthesizing a
story. Part  of their value  is their judgement  in presenting you  with the essential  facts, and until they  prove they can't  synthesize well, you  assume they can.  Second, and
contradictorily, while I believe that folks don't wake up intending to construct lies, I also know that for any story you're hearing, you're getting the version that supports their
chosen version of reality. As a story is being told to you, the opinion of the  storyteller is affecting both the content and the tone. Their agenda dictates what they are choosing
to tell you. Again, malevolent forces are not necessarily driving the storyteller. They are  hopeful, they want to succeed, but this story needs judgment, and that's where you come
in as a manager. I'll explain by example. A Familiar Nail "Ok, Project Frodo -- we're two weeks from feature complete. Our task list is down to seven items, but as you can see from
this chart, the work is spread out among  the teams. I'm confident we'll hit the date." This sounds like good news. This sounds like  the truth. Nothing in those three sentences is
setting off any alarms in my head, but I'm a manager and it's my job to sniff around.  "Is the design done?" "Yes, except for items six and seven." Ok, so it's not done. "When will
they be done  with design?" "In a  week and half." "And you  can get the tasks  done in the two days  after we receive the designs?"  "I, uh..." Sniffing around  pisses people off.
Sniffing around is often interpreted as micromanagement, a passive aggressive way of stating, "I don't believe you can do your job." While there are a great many managers out there
who pull this move as  a means of pumping up their fading value, this  is not what I'm doing -- I'm trying to  figure out if this story is familiar. I've built  a lot of teams that
have built a  lot of software. I know  that what we receive as complete  designs is usually 80% of  what we actually need. Because  I was the engineer sitting there  staring at the
Photoshops in the middle of  the night with two days to feature complete, thinking,  "It's sure pretty, but what about internationalization? And error  cases? You know that's work,
right?" It's not that I know  all the intricacies of Project Frodo and I don't want  to know them. It's a team full of personalities, tasks, and  dependencies that I could spend my
entire day trying to understand, and I've got two other projects of equal size that are  running hot. As I'm listening to this story, I'm listening hard and trying to figure out...
have  I  seen  this  nail   before?  I  have,  haven't  I?  I  don't  remember  when,   but  I  do  remember  the  Twinge...  Do  you  remember   every  success  and  failure?  No.
"""


class SentenceSpeakerTest(TestCase):

    def test(self):
        speaker = SentenceSpeaker()
        speaker.ingest(_text)
        for i in xrange(10):
            print "[%d] %s" % (i, speaker.speak(0, 130))


if __name__ == "__main__":
    main()