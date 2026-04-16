import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_transcript(video_id):
    try:
        print(f"Fetching transcript for video ID: '{video_id}'...")
        # Fetch the transcript
        yt_api = YouTubeTranscriptApi()
        
        # In newer versions of youtube_transcript_api, we use list/fetch. 
        # The fetch method returns a FetchedTranscript object which is iterable.
        transcript_list = yt_api.list(video_id)
        transcript = transcript_list.find_transcript(['en']).fetch()
        
        # Format the transcript as plain text
        formatter = TextFormatter()
        text_transcript = formatter.format_transcript(transcript)
        
        print("\n--- Transcript Preview ---\n")
        # Print the first 500 characters of the transcript as a preview
        if len(text_transcript) > 500:
            print(text_transcript[:500] + "\n... [truncated] ...")
        else:
            print(text_transcript)
            
        print("\nSuccessfully fetched transcript!")
        return text_transcript
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example video ID (Rick Astley - Never Gonna Give You Up)
    # You can change this to any YouTube video ID you want to test!
    sample_video_id = "dQw4w9WgXcQ" 
    
    if len(sys.argv) > 1:
        sample_video_id = sys.argv[1]
        
    get_transcript(sample_video_id)
