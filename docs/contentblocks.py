# coding: utf-8


from dataclasses import dataclass

@dataclass
class Featured:
    name: str
    title: str
    url: str
    icon: str
    lead_text: str


@dataclass
class Author:
    name: str
    display: str
    description: str
    twitter_handle: str = ""
    image: str = ""



# Site metadata
HERO_TITLE = "Bookworm"
HERO_LEAD = "The universally accessible document reader"
FEATURED = (
    Featured(
        name="software",
        title="Software",
        url="software",
        icon="fa-gifts",
        lead_text="We develop free, open-source, and highly accessible applications for blind and visually impaired computer users."
    ),
    Featured(
        name="training",
        title="Traning",
        url="training",
        icon="fa-chalkboard-teacher",
        lead_text=(
            "We offer tutorials and booklets on selected programming topics for the next generation of blind and visually impaired makers.",
        )
    ),
    Featured(
        name="advocacy",
        title="Advocacy",
        url="advocacy",
        icon="fa-hands-helping",
        lead_text="The world runs on open-source. We develop accessible apps and teach open-source developers on how to do the same."
    ),
    Featured(
        name="mentoring",
        title="Mentoring",
        url="mentoring",
        icon="fa-users-cog",
        lead_text="We provide a hub to connect volunteering mentors to junior programmers who are interested in accessibility."
    ),
)

# Main navigation menu
MAIN_NAVIGATION_MENU = [("Blog", "blog"),]

# Twitter embed
TWITTER_USER = 'blindpandas'
TWITTER_EMBED_TITLE = "Tweets by Blind Pandas Team"
TWITTER_EMBED_WIDTH = 500
TWITTER_EMBED_HEIGHT= 500

# Social links
SOCIAL_LINKS = (
    ("Twitter", "https://twitter.com/blindpandas/", "twitter fab"),
    ("GitHub", "https://github.com/blindpandas/bookworm", "github fab"),
    ("Users Mailing List", "https://groups.io/g/blindpandas-users", "envelope fa"),
)

AUTHORS = {
    "Musharraf": Author(
        name="Musharraf",
        display="Musharraf Omer",
        description="Musharraf is the founder of Blind Pandas Team and the lead developer of Bookworm, the universally accessible document reader.",
        twitter_handle="mush42",
        image="static/images/authors/musharraf.jpg",
    )
}