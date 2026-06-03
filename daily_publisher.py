import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Ross and Rachel — The Will They/Won't They That Defined a Generation",
        "The One Where Chandler Gets Unforgettably Sarcastic",
        "Joey's Best 'How You Doin'?' Moments You Need to See",
        "Phoebe's Most Iconic and Quirky Moments on Friends",
        "Monica's Best Obsessive Moments — So Relatable",
        "The Funniest Friends Bloopers and Behind-the-Scenes",
        "Central Perk — The Iconic Coffee Shop We All Wish Was Real",
        "Friends' Most Emotional Scenes That Made Us All Cry",
        "The One With All the Thanksgiving Disasters",
        "Ross Geller — The Unluckiest Man in TV History",
        "Rachel Green's Best 90s Fashion Moments — Style Icon",
        "Friends Cast Then vs Now — Where Are They Today?",
        "Chandler Bing — The King of Sarcasm's Best One-Liners",
        "The One Where We All Wish We Were Part of the Gang",
        "PIVOT! — Ross's Most Frustratingly Funny Moments",
    ]

    fallback_descriptions = [
        "Ross and Rachel – the greatest will-they-won't-they in TV history. From the first kiss at Central Perk to the iconic 'I got off the plane' finale, their story spanned a decade of ups, downs, breakups, and makeups. David Schwimmer and Jennifer Aniston had chemistry that is still unmatched to this day. It's the relationship that kept us watching season after season. Drop a ❤️ if you're team Ross and Rachel! #friends #rossandrachel #rossgeller #rachelgreen #tvshow #90s #nostalgia #centralperk #friendsforever #iconiccouple #friendsfan #tvhistory #nbc #sitcom",
        "Chandler Bing – the sarcastic legend we didn't know we needed. His one-liners, his awkward humor, and his incredible character growth from commitment-phobe to the best husband and dad. Remember 'Could I BE any more...'? That voice, that delivery, those perfectly timed jokes. Matthew Perry brought Chandler to life in a way that made us laugh and cry. Like if Chandler Bing is your favorite Friends character! 😂 #friends #chandlerbing #matthewperry #couldibeanymore #tvfunny #sitcom #90s #comedy #chandler #friendsfan #sarcasm #legend #nbc",
        "Phoebe Buffay – the most unique, quirky, and lovable character on Friends. From writing 'Smelly Cat' to her bizarre yet somehow wise life advice, Phoebe marched to the beat of her own drum. Lisa Kudrow's comedic timing was absolutely perfect. She could make you laugh with a single eyebrow raise and then break your heart with her emotional moments. Comment your favorite Phoebe moment below! 🎸 #friends #phoebebuffay #lisakudrow #smellycat #quirky #tvfunny #sitcom #90s #phoebe #friendsfan #unique #iconic #nbc",
        "Monica Geller – the competitive, obsessive, lovable perfectionist we all relate to. Her need for organization, her legendary Thanksgiving disasters, and her incredible journey from overeating to becoming a top chef. Courteney Cox brought so much heart and humor to the role. Whether she's cleaning frantically or yelling 'I KNOW!' – Monica is the glue that holds the group together. Share this if you're a Monica energy person! 🧹 #friends #monicageller #courteneycox #cleanfreak #tvshow #sitcom #90s #chef #monica #friendsfan #relatable #organized #nbc",
        "Joey Tribbiani – the actor, the food lover, the ultimate loyal friend. 'How you doin'?' is just the beginning. Joey's love for food, his childlike innocence, and his unwavering loyalty to his friends made him unforgettable. Matt LeBlanc's comedic genius turned Joey into one of the most beloved characters of all time. The way he says 'Hey, how you doin'?' still makes us smile. Drop a 🍕 if you love Joey! #friends #joeytribbiani #mattleblanc #howyoudoin #tvfunny #sitcom #90s #actor #joey #friendsfan #foodie #loyal #nbc",
        "The funniest Friends bloopers and behind-the-scenes moments you've ever seen! The cast had incredible chemistry both on and off screen. From laughing fits during serious scenes to improvised lines that became legendary, this show was pure magic. Jennifer Aniston, Courteney Cox, Lisa Kudrow, Matt LeBlanc, Matthew Perry, and David Schwimmer were more than co-stars – they were family. Like if you wish you could've been on the Friends set! 🎬 #friends #bloopers #bts #friendsbloopers #laughs #tvshow #behindthescenes #cast #jenniferaniston #courteneycox #lisakudrow #mattleblanc #matthewperry #davidschwimmer",
        "Central Perk – the iconic orange couch, the coffee cups, and the place where everything happened. That coffee shop was practically the seventh friend. The ambiance, the regulars (hello Gunther!), the live music performances, and all the deep conversations that happened over coffee. It's the hangout spot we all wished existed in real life. Follow for more Friends nostalgia! ☕ #friends #centralperk #coffee #90s #tvshow #gunther #orangecouch #nostalgia #friendsfan #iconic #sitcom #nbc",
        "The most emotional scenes from Friends that made us all ugly cry. From Ross and Rachel's first breakup to Monica and Chandler's proposal, from Phoebe's surrogate birth to the final goodbye in Monica's empty apartment. This show knew how to hit you right in the feels. The acting, the music, the writing – perfection. Comment which Friends scene made YOU cry the most! 😢 #friends #emotional #sadfriends #rossandrachel #monicaandchandler #tvshow #90s #cry #nostalgia #friendsfan #heartfelt #finale #nbc",
        "Friends Thanksgiving episodes were always the best! From the trifle that had meat and dessert in the same dish to Ross's 'MY SANDWICH?!' meltdown, every holiday episode was comedy gold. The football game, Monica's flawless cooking, the Geller Cup – Thanksgiving was never boring with this crew. Like if Friends made your Thanksgivings better! 🦃 #friends #thanksgiving #friendsgiving #trifle #mysandwich #tvshow #90s #sitcom #holiday #comedy #classic #nbc",
        "Ross Geller – the unluckiest but most lovable paleontologist on TV. From his three divorces to 'WE WERE ON A BREAK!', from playing the keyboard to the leather pants disaster, Ross's life was one hilarious tragedy after another. But David Schwimmer's physical comedy and emotional range made Ross one of the most memorable characters ever. 'PIVOT!', 'UNAGI!', 'I'm fine!' – all legendary. Drop a 🦴 if Ross is underrated! #friends #rossgeller #davidschwimmer #pivot #dinosaurs #tvshow #90s #ross #friendsfan #underrated #comedygenius #nbc",
        "Rachel Green's fashion evolution is the ultimate 90s style inspiration. From her Central Perk waitress uniform to her Ralph Lauren power suits, from the iconic 'Rachel' haircut to her stunning maternity wear – she defined a decade of fashion. Jennifer Aniston made Rachel a style icon that people still copy today. High-waisted jeans, slip dresses, crop tops – Rachel wore it all and made it look effortless. Follow for style inspo from Rachel Green! 👗 #friends #rachelgreen #jenniferaniston #90sfashion #styleicon #rachelhaircut #tvshow #fashion #90s #nostalgia #rachel #friendsfan #nbc",
        "Friends cast then vs now – where are they today? Jennifer Aniston is still a massive Hollywood star. Courteney Cox starred in Scream and continues acting. Lisa Kudrow is still making us laugh. Matt LeBlanc had his own spin-off. David Schwimmer directs and acts. And while we lost Matthew Perry far too soon, his legacy as Chandler Bing lives on forever. This cast defined a generation. Share this to honor the Friends cast! ⭐ #friends #friendscast #thenvsnow #jenniferaniston #courteneycox #lisakudrow #mattleblanc #matthewperry #davidschwimmer #nostalgia #tvshow #90s #hollywood",
        "Chandler Bing's best one-liners that still live rent-free in our heads. 'Could I BE any more...?', 'I'm not great at the advice... can I interest you in a sarcastic comment?', 'I wish I could, but I don't want to.' His sarcasm was an art form and Matthew Perry delivered each line with perfect timing. He had the best character arc too – from using humor as a shield to becoming a loving husband and father. Drop your favorite Chandler quote below! 🗣️ #friends #chandlerbing #matthewperry #sarcasm #one-liners #tvfunny #sitcom #90s #chandler #friendsfan #funny #bestquotes",
        "The one where we all wish we were part of the group. Friends wasn't just a show – it was a feeling. It was the comfort of knowing your people are always there for you. The laughs, the fights, the makeups, and the love – it was everything. Twenty years later, we're still watching, still laughing, still crying. Because Friends is timeless. Like if Friends is your comfort show! 💛 #friends #tvshow #comfortshow #90s #nostalgia #friendsforever #friendsfan #iconic #timeless #nbc #centralperk #bestshow",
        "PIVOT! – Ross's most frustratingly funny moments in one video. From moving the couch up the stairs to the leather pants incident with the lotion, from his spray tan disaster ('They came out of a GUN!') to the infamous 'I'm FINE' meltdown. David Schwimmer is a master of physical comedy. These moments are so cringe but so hilarious at the same time. Comment your most cringey Ross moment! 😂 #friends #rossgeller #davidschwimmer #pivot #cringe #tvfunny #sitcom #90s #ross #friendsfan #physicalcomedy #funnymoments",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory — hype up the best Friends moments and character highlights",
        "fun and engaging — make it feel like you're reminiscing about the show with a fellow fan",
        "inspiring and uplifting — highlight how the friendships and bonds inspire viewers",
        "nostalgic and throwback — celebrate the 90s classic and the memories it brings",
        "emotional and heartfelt — showcase the powerful scenes and moments that made us cry",
        "funny and lighthearted — capture the hilarious comedy and legendary one-liners",
        "nostalgic and throwback — celebrate Friends as the greatest sitcom of all time",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about the TV series Friends for the Facebook page 'Friends Forever'. "
        f"The page posts the best Friends moments — hilarious scenes, emotional moments, character highlights, "
        f"bloopers, iconic quotes, and everything that makes Friends the greatest sitcom ever. "
        f"Speak as a passionate Friends fan who loves celebrating the show. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Friends! "
        f"- Comment your favorite Friends character! "
        f"- Share this with another Friends fan! "
        f"- Follow Friends Forever for the best Friends content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #friends #tvshow #90s #nostalgia #rossgeller #rachelgreen #chandlerbing #monicageller #joeytribbiani #phoebebuffay #centralperk #sitcom #nbc #friendsforever #friendsfan #comedy #iconic. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["friends", "tvshow", "90s", "nostalgia", "rossgeller", "rachelgreen", "chandlerbing", "monicageller", "joeytribbiani", "phoebebuffay", "centralperk", "sitcom", "nbc", "friendsforever", "friendsfan", "comedy", "iconic"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
