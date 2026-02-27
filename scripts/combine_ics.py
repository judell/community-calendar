#!/usr/bin/env python3
"""
Combine multiple ICS files into a single subscribable calendar feed.
Filters to only include events from today forward.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# Map filenames to friendly source names.
# Only needed when the filename doesn't convert cleanly via stem.replace('_', ' ').title().
# For example, 'arlene_francis_theater' -> 'Arlene Francis Theater' misses 'Center',
# so we override it here. Most sources don't need an entry.
SOURCE_NAMES = {
    'arlene_francis_theater': 'Arlene Francis Center',
    'luther_burbank_center': 'Luther Burbank Center',
    'schulz_museum': 'Charles M. Schulz Museum',
    'sonoma_com': 'Sonoma.com',
    'golocal_coop': 'GoLocal Cooperative',
    'sonoma_county_aa': 'Sonoma County AA',
    'sonoma_county_dsa': 'Sonoma County DSA',
    'museumsc': 'Museum of Sonoma County',
    'library_intercept': 'Sonoma County Library',
    'sonoma_county_gov': 'Sonoma County Government',
    'sonoma_parks': 'Sonoma County Parks',
    'cal_theatre': 'Cal Theatre',
    'copperfields': "Copperfield's Books",
    'bohemian': 'North Bay Bohemian',
    'pressdemocrat': 'Press Democrat',
    # Meetup groups - Santa Rosa
    'meetup_go_wild_hikers': 'Meetup: Go Wild Hikers',
    'meetup_shutupandwrite': 'Meetup: Shut Up & Write Wine Country',
    'meetup_scottish_dancing': 'Meetup: Scottish Country Dancing',
    'meetup_womens_wine_club': 'Meetup: Women\'s Wine Club',
    'meetup_toastmasters': 'Meetup: Santa Rosa Toastmasters',
    'meetup_yoga': 'Meetup: Nataraja Yoga',
    'meetup_creativity': 'Meetup: Women\'s Creativity Collective',
    'meetup_boomers': 'Meetup: Sonoma County Boomers',
    # Meetup groups - Davis
    'meetup_mosaics': 'Meetup: Mosaics',
    'meetup_intercultural': 'Meetup: Intercultural Mosaics',
    'meetup_board_games': 'Meetup: Yolo Board Game Gathering',
    'meetup_pence_art': 'Meetup: Pence Art Programs',
    'meetup_art_in_action': 'Meetup: Art in Action',
    'meetup_mindful': 'Meetup: Mindful Embodied Spirituality',
    'meetup_winters_write': 'Meetup: Winters Shut Up & Write',
    'SRCity': 'City of Santa Rosa',
    'legistar': 'City of Santa Rosa Legistar',
    'srcc': 'Santa Rosa Cycling Club',
    'cafefrida': 'Cafe Frida',
    'barrel_proof': 'Barrel Proof Lounge',
    'sportsbasement': 'Sports Basement',
    'sebastopol_community': 'Sebastopol Community Center',
    'redwood_cafe': 'Redwood Cafe',
    'sebarts': 'Sebastopol Center for the Arts',
    'rileystreet_art': 'Riley Street Art Supply',
    'srjc': 'Santa Rosa Junior College',
    'meetup_amorc': 'AMORC Santa Rosa Pronaos',
    'meetup_sarogn': 'SAROGN',
    'occidental_arts': 'Occidental Arts & Ecology Center',
    'svma': 'Sonoma Valley Museum of Art',
    'sonoma_city': 'City of Sonoma',
    'bgc_bloomington': 'Boys & Girls Club Bloomington',
    'bloomington_gov': 'City of Bloomington',
    'bloomington_arts': 'Bloomington Arts',
    'calendar_cuc66guoam1hhcqq2rnaniinl8_40group_calend': 'Bloomington Bicycle Club',
    'bluebird': 'The Bluebird',
    'iu_jacobs_music': 'IU Jacobs School of Music',
    'iu_auditorium': 'IU Auditorium',
    'iu_eskenazi_museum': 'Eskenazi Museum of Art',
    'bsquare_government': 'Bloomington Government',
    'bsquare_misc_civic': 'Bloomington Civic Events',
    'bsquare_critical_mass': 'Critical Mass Bloomington',
    'bsquare_bptc': 'Bloomington Public Transit',
    # Petaluma
    'petaluma_downtown': 'Petaluma Downtown Association',
    'meetup_mindful_petaluma': 'Meetup: Mindful Petaluma',
    'meetup_rebel_craft': 'Meetup: Rebel Craft Collective',
    'meetup_candlelight_yoga': 'Meetup: Candlelight Yoga Petaluma',
    'meetup_figure_drawing': 'Meetup: Petaluma Figure Drawing',
    'meetup_brat_pack': 'Meetup: Sonoma-Marin Brat Pack',
    'aqus_community': 'Aqus Community',
    'mystic_theatre': 'Mystic Theatre',
    'maxpreps_petaluma_high': 'Petaluma High School Athletics',
    'maxpreps_casa_grande': 'Casa Grande High School Athletics',
    # Santa Rosa High Schools (MaxPreps)
    'maxpreps_santa_rosa_high': 'Santa Rosa High School Athletics',
    'maxpreps_montgomery_high': 'Montgomery High School Athletics',
    'maxpreps_maria_carrillo': 'Maria Carrillo High School Athletics',
    'maxpreps_piner_high': 'Piner High School Athletics',
    'maxpreps_elsie_allen': 'Elsie Allen High School Athletics',
    'maxpreps_cardinal_newman': 'Cardinal Newman High School Athletics',
    'petaluma_chamber': 'Petaluma Chamber of Commerce',
    'meetup_petaluma_salon': 'Meetup: Petaluma Salon',
    'meetup_book_brew': 'Meetup: Petaluma Book & Brew Club',
    'meetup_active_20_30': 'Meetup: Petaluma Active 20-30',
    'srjc_petaluma': 'SRJC Petaluma Campus',
    'bigeasy': 'The Big Easy',
    'polly_klaas': 'Polly Klaas Community Theater',
    'brooksnote': 'Brooks Note Winery',
    'petaluma_arts_center': 'Petaluma Arts Center',
    'brewsters': 'Brewsters Beer Garden',
    'cool_petaluma': 'Cool Petaluma',
    'mcnears': "McNear's Saloon",
    'griffo': 'Griffo Distillery',
    'elks_lodge': 'Petaluma Elks Lodge',
    'garden_club': 'Petaluma Garden Club',
    'petaluma_bounty': 'Petaluma Bounty',
    # Santa Rosa - local arts/community
    'santa_rosa_arts_center': 'Santa Rosa Arts Center',
    'movingwriting': 'MovingWriting',
    # Toronto - Aggregators
    'now_toronto': 'NOW Toronto',
    'torevent': 'Toronto Events (Tockify)',
    # Toronto - Music Venues
    'jazz_bistro': 'Jazz Bistro',
    'grossmans_tavern': "Grossman's Tavern",
    # Toronto - Venues & Institutions
    'union_station': 'Union Station Toronto',
    'distillery_events': 'Distillery District',
    'gardiner_museum': 'Gardiner Museum',
    'toronto_botanical': 'Toronto Botanical Garden',
    'textile_museum': 'Textile Museum of Canada',
    'bata_shoe_museum': 'Bata Shoe Museum',
    'buddies_theatre': 'Buddies in Bad Times Theatre',
    'factory_theatre': 'Factory Theatre',
    'high_park_nature': 'High Park Nature Centre',
    # Toronto - Universities
    'york_university': 'York University',
    'uoft_events': 'University of Toronto',
    'uoft_engineering': 'UofT Engineering',
    'uoft_philosophy': 'UofT Philosophy',
    'uoft_socialwork': 'UofT Social Work',
    # Toronto - Community Organizations
    'culturelink': 'CultureLink Settlement Services',
    'scadding_court': 'Scadding Court Community Centre',
    'st_lawrence_na': 'St. Lawrence Neighbourhood Association',
    'bloor_west_village': 'Bloor West Village BIA',
    'jamaalmyers': 'Councillor Jamaal Myers',
    'showup_toronto': 'Show Up Toronto',
    # Toronto - Meetup groups
    'meetup_sai_dham_volunteer': 'Meetup: SAI Dham Canada Toronto Volunteer Group',
    'meetup_toronto_dads': 'Meetup: Toronto Dads Group',
    'meetup_little_sunbeams': 'Meetup: Little Sunbeams (Parents + Tots)',
    'meetup_mini_me': 'Meetup: Mini + Me Meetups',
    'meetup_torontobabel': 'Meetup: TorontoBabel Language Exchange',
    'meetup_try_new_things': 'Meetup: Try New Things in Toronto',
    'meetup_arts_culture': 'Meetup: Toronto Arts & Culture',
    'meetup_hiking_boots': 'Meetup: These Boots Are Made for Hiking',
    'meetup_bike_toronto': 'Meetup: Toronto Bike Meetup',
    'meetup_board_games_to': 'Meetup: Board Games and Social',
    'meetup_salsa_gta': 'Meetup: Salsa/Bachata/Kizomba GTA',
    'meetup_photography_to': 'Meetup: Toronto Photography Group',
    'meetup_book_club_abcd': 'Meetup: A Book Club Downtown',
    'meetup_improv_to': 'Meetup: Improv, Acting & Karaoke',
    'meetup_techto': 'Meetup: TechTO',
    'meetup_torontojs': 'Meetup: Toronto JavaScript',
    'meetup_python_to': 'Meetup: Python Toronto',
    # Toronto - Crafts & Makers
    'repair_cafe_toronto': 'Repair Cafe Toronto',
    'knitters_guild': 'Toronto Knitters Guild',
    'site3': 'Site 3 CoLaboratory',
    'meetup_3d_printing': 'Meetup: Toronto 3D Printing',
    'meetup_arts_crafts': 'Meetup: Midtown Arts & Crafts',
    # Toronto - Government & Public Affairs
    'toronto_meetings': 'City of Toronto Meetings',
    'toronto_festivals': 'City of Toronto Festivals & Events',
    'volunteer_toronto': 'Volunteer Toronto',
    'tpl_events': 'Toronto Public Library',
    'cita_local_events': 'CITA Local Events',
    'cita_seminars': 'CITA Seminars',
    'cita_special_events': 'CITA Special Events',
    # Toronto - Outdoor & Nature
    'ontario_nature': 'Ontario Nature',
    'meetup_founders_running': 'Meetup: Founders Running Club Toronto',
    'meetup_high_park_yoga': 'Meetup: High Park Yoga',
    'meetup_mindful_movement': 'Meetup: Mindful Movement Toronto',
    'meetup_toronto_wellness': 'Meetup: Toronto Wellness',
    'meetup_sup_kayak': 'Meetup: Toronto SUP, Kayak & Canoe',
    'meetup_toronto_paddlers': 'Meetup: Toronto Paddlers',
    'meetup_canoe_trippers': 'Meetup: Toronto Canoe Trippers',
    'meetup_20s30s_social': 'Meetup: 20s 30s Toronto Social',
    'meetup_soul_city': 'Meetup: Soul City Social Club',
    'meetup_experience_to': 'Meetup: Experience Toronto',
    'meetup_hiking_network': 'Meetup: Hiking Network',
    'meetup_gta_hiking': 'Meetup: GTA Hiking & Stuff',
    'meetup_bruce_trail': 'Meetup: Toronto Bruce Trail Club',
    'meetup_wilderness_union': 'Meetup: Wilderness Union',
    'meetup_heavy_boardgames': 'Meetup: Toronto Heavy Boardgamers',
    'meetup_movies_social': 'Meetup: Toronto Movies & Social',
    'meetup_scifi_books': 'Meetup: Sci Fi Book Club',
    'meetup_postapoc_books': 'Meetup: Post-Apocalyptic Book Club',
    'meetup_silent_books': 'Meetup: Silent Book Club',
    'meetup_jpn_eng_exchange': 'Meetup: Toronto Japanese English Exchange',
    'meetup_lang_exchange_to': 'Meetup: Language Exchange Toronto',
    'meetup_tile_language': 'Meetup: TILE Language Party',
    'meetup_improv_friends': 'Meetup: Improv For New Friends',
    'meetup_ai_ml': 'Meetup: Toronto AI & ML',
    'meetup_ms_reactor': 'Meetup: Microsoft Reactor Toronto',
    'meetup_tech_stack': 'Meetup: Toronto Tech Stack Exchange',
    'meetup_devops': 'Meetup: Toronto Enterprise DevOps',
    'meetup_postgres_to': 'Meetup: Toronto Postgres',
    'meetup_women_biz': 'Meetup: Toronto Women in Business',
    'meetup_singles_social': 'Meetup: Toronto 20s-50s Singles Social',
    # Raleigh-Durham
    'unc_chapel_hill': 'UNC Chapel Hill',
    'ncsu': 'NC State University',
    'duke': 'Duke University',
    'nc_cultural_resources': 'NC Cultural Resources',
    'ackland_art': 'Ackland Art Museum',
    'nc_botanical_garden': 'NC Botanical Garden',
    'nasher_museum': 'Nasher Museum of Art',
    'triangle_land': 'Triangle Land Conservancy',
    'durham_central_park': 'Durham Central Park',
    'durham_library': 'Durham County Library',
    'durham_gov': 'City of Durham',
    'duke_gardens': 'Sarah P. Duke Gardens',
    'nc_natural_sciences': 'NC Museum of Natural Sciences',
    'durham_chamber': 'Durham Chamber of Commerce',
    'wakeforest_chamber': 'Wake Forest Chamber of Commerce',
    'apex_chamber': 'Apex Chamber of Commerce',
    'wake_county_legistar': 'Wake County Government',
    'chapelhill_legistar': 'Town of Chapel Hill',
    'durhamcounty_legistar': 'Durham County Government',
    'meetup_tripython': 'Meetup: Triangle Python Users',
    'meetup_pydata_triangle': 'Meetup: PyData Triangle',
    'meetup_research_triangle_analysts': 'Meetup: Research Triangle Analysts',
    'meetup_triangleai': 'Meetup: Triangle AI',
    'meetup_triangle_devs': 'Meetup: Triangle Developers',
    'meetup_all_things_open_rtp_meetup': 'Meetup: All Things Open RTP',
    'meetup_triangle_techbreakfast': 'Meetup: Triangle TechBreakfast',
    'meetup_futureofdata_triangle': 'Meetup: Future of Data Triangle',
    'meetup_blacks_in_tech_bit_rdu_durham_raleigh_meetup': 'Meetup: Blacks in Tech RDU',
    'meetup_downtown_techies_durham': 'Meetup: Downtown Techies Durham',
    'meetup_raleigh_wordpress_meetup_group': 'Meetup: Raleigh WordPress',
    'meetup_adventures': 'Meetup: Triangle Hiking & Outdoors',
    'meetup_durham_geeks': 'Meetup: Durham Geeks',
    'meetup_durham_board_games_meetup_group': 'Meetup: Durham Board Games',
    'meetup_chad2015': 'Meetup: CHAD (Chapel Hill & Durham Fun)',
    'meetup_discover_durham_together': 'Meetup: Discover Durham Together',
    'meetup_chicktech_rdu': 'Meetup: ChickTech RDU',
    'meetup_raleigh_triangle_activities': 'Meetup: Raleigh & Triangle Activities',
    'meetup_code_for_america': 'Meetup: Code with the Carolinas',
    'transitions_lifecare': 'Transitions LifeCare',
    'nc_wildlife_federation': 'NC Wildlife Federation',
    'resilient_durham': 'Resilient Durham NC',
    'sw_durham_rotary': 'SW Durham Rotary Club',
    # Raleigh-Durham - Birding & Nature (Google Calendar)
    'wake_audubon': 'Wake Audubon',
    'new_hope_bird_alliance': 'New Hope Bird Alliance',
    'eno_river': 'Eno River Association',
    # Raleigh-Durham - Downtown Durham
    'downtown_durham': 'Downtown Durham Inc',
    # Raleigh-Durham - Health & Well-Being
    'meetup_yoga_in_nature': 'Meetup: Yoga In Nature NC',
    'meetup_outdoor_flow_yogis': 'Meetup: Outdoor Flow Yogis',
    'meetup_plum_village_meditation': 'Meetup: Durham Plum Village Meditation',
    # Raleigh-Durham - Animals & Rescue
    'independent_animal_rescue': 'Independent Animal Rescue',
    'hope_animal_rescue': 'Hope Animal Rescue',
    'aps_durham': 'Animal Protection Society of Durham',
    'second_chance_pets': 'Second Chance Pet Adoptions',
    # Raleigh-Durham - Play & Games
    'meetup_triangle_board_games': 'Meetup: Triangle Board Games & Bars',
    'gathering_place_games': 'The Gathering Place Games',
    # Raleigh-Durham - Ideas & Learning
    'morehead_planetarium': 'Morehead Planetarium & Science Center',
    'nc_humanities': 'NC Humanities Council',
    'meetup_durham_writers': 'Meetup: Durham Writers Group',
    'american_tobacco_campus': 'American Tobacco Campus',
    # Raleigh-Durham - Technology & Work (additional Meetups)
    'meetup_raleigh_ai_ml_cv': 'Meetup: Raleigh AI, ML & Computer Vision',
    'meetup_all_things_ai': 'Meetup: All Things AI',
    'meetup_data_science_raleigh': 'Meetup: Data Science Raleigh',
    'meetup_modern_web_triangle': 'Meetup: Modern Web Triangle',
    'meetup_triangle_devops': 'Meetup: Triangle DevOps',
    'meetup_splatspace': 'Meetup: Splat Space (Durham Hackerspace)',
    'meetup_csa_triangle': 'Meetup: Cloud Security Alliance Triangle',
    'meetup_triangle_transitional': 'Meetup: Triangle Transitional Networking',
    # Raleigh-Durham - Squarespace scrapers
    'ponysaurus': 'Ponysaurus Brewing',
    'scrap_exchange': 'The Scrap Exchange',
    'keep_durham_beautiful': 'Keep Durham Beautiful',
    'haw_river_assembly': 'Haw River Assembly',
    'catscradle': "Cat's Cradle",
    'motorco': 'Motorco Music Hall',
    'carolina_theatre': 'Carolina Theatre',
    'carolina_performing_arts': 'Carolina Performing Arts',
    'duke_arts': 'Duke Arts',
    'raleigh_little_theatre': 'Raleigh Little Theatre',
    'durham_resistance_1': 'Durham Resistance',
    'durham_resistance_2': 'Durham Resistance',
    'durham_resistance_3': 'Durham Resistance',
    'durham_resistance_4': 'Durham Resistance',
    'bike_durham': 'Bike Durham',
    'triangle_cycling': 'Triangle Cycling',
    'gizmo_brew_works': 'Gizmo Brew Works',
    'lgbtq_center_durham': 'LGBTQ Center of Durham',
    'eno_river': 'Eno River Association',
    'new_hope_bird_alliance': 'New Hope Bird Alliance',
    'wake_audubon': 'Wake Audubon',
    'sw_durham_rotary': 'SW Durham Rotary',
    'durham_gov': 'City of Durham',
    'durham_gov_community': 'City of Durham',
    'buskirk_chumley': 'Buskirk-Chumley Theater',
    'comedy_attic': 'The Comedy Attic',
    'the_bishop': 'The Bishop',
    'peoples_market': "People's Market",
    'lotusfest': 'Lotus Festival',
    'spreckels': 'Spreckels Performing Arts Center',
    'lagunitas': 'Lagunitas Brewing Company',
    'creative_sonoma': 'Creative Sonoma',
    'cinnabar': 'Cinnabar Theater',
    'green_music_center': 'Green Music Center',
    'jack_london_park': 'Jack London State Historic Park',
}

# Fallback URLs for sources whose ICS events lack a URL property.
# Only needed for scraped sources where per-event URLs aren't available.
SOURCE_URLS = {
    'arlene_francis_theater': 'https://arlenefranciscenter.org/calendar/',
    'luther_burbank_center': 'https://lutherburbankcenter.org/events/',
    'schulz_museum': 'https://schulzmuseum.org/events/',
    'sonoma_com': 'https://www.sonoma.com/events/',
    'golocal_coop': 'https://golocal.coop/events/',
    'sonoma_county_aa': 'https://sonomacountyaa.org/events/',
    'sonoma_county_dsa': 'https://dsasonomacounty.org/events/',
    'library_intercept': 'https://sonomalibrary.org/events',
    'sonoma_county_gov': 'https://sonomacounty.ca.gov/calendar/',
    'sonoma_parks': 'https://parks.sonomacounty.ca.gov/events/',
    'cal_theatre': 'https://www.facebook.com/CalTheatrePT/',
    'copperfields': 'https://www.copperfieldsbooks.com/events',
    # Santa Rosa venues/organizations
    'bohemian': 'https://bohemian.com/events-calendar/',
    'pressdemocrat': 'https://www.pressdemocrat.com/events/',
    'cafefrida': 'https://www.cafefrida.com/',
    'srcc': 'https://srcc.memberlodge.com/page-1363886',
    'barrel_proof': 'https://www.barrelprooflounge.com/live-events',
    'sportsbasement': 'https://www.sportsbasement.com/pages/santa-rosa',
    'sebarts': 'https://www.sebarts.org/calendar/',
    'legistar': 'https://santa-rosa.legistar.com/Calendar.aspx',
    'spreckels': 'https://www.spreckelsonline.com/events/',
    'lagunitas': 'https://lagunitas.com/taproom/petaluma',
    'creative_sonoma': 'https://creativesonoma.org/events/',
    'cinnabar': 'https://www.cinnabartheater.org/whats-on/',
    'green_music_center': 'https://gmc.sonoma.edu/events/',
    'rileystreet_art': 'https://www.rileystreet.com/pages/santa-rosa-classes-events',
    'srjc': 'https://calendar.santarosa.edu/',
    'museumsc': 'https://museumsc.org/events/',
    # Santa Rosa MaxPreps high schools
    'maxpreps_santa_rosa_high': 'https://www.maxpreps.com/ca/santa-rosa/santa-rosa-panthers/',
    'maxpreps_montgomery_high': 'https://www.maxpreps.com/ca/santa-rosa/montgomery-vikings/',
    'maxpreps_maria_carrillo': 'https://www.maxpreps.com/ca/santa-rosa/maria-carrillo-pumas/',
    'maxpreps_piner_high': 'https://www.maxpreps.com/ca/santa-rosa/piner-prospectors/',
    'maxpreps_elsie_allen': 'https://www.maxpreps.com/ca/santa-rosa/elsie-allen-lobos/',
    'maxpreps_cardinal_newman': 'https://www.maxpreps.com/ca/santa-rosa/cardinal-newman-cardinals/',
    # Santa Rosa Meetup groups
    'meetup_go_wild_hikers': 'https://www.meetup.com/sonoma-county-go-wild-hikers/',
    'meetup_shutupandwrite': 'https://www.meetup.com/shutupandwritewinecountry/',
    'meetup_scottish_dancing': 'https://www.meetup.com/scottish-country-dancing/',
    'meetup_womens_wine_club': 'https://www.meetup.com/sonoma-county-womens-wine-club/',
    'meetup_toastmasters': 'https://www.meetup.com/santa-rosa-toastmasters-public-speaking-meetup-group/',
    'meetup_yoga': 'https://www.meetup.com/nataraja-school-of-traditional-yoga/',
    'meetup_creativity': 'https://www.meetup.com/santa-rosa-womens-creativity-collective/',
    'meetup_boomers': 'https://www.meetup.com/sonoma-county-boomers/',
    'meetup_amorc': 'https://www.meetup.com/amorc-santa-rosa-pronaos/',
    'meetup_sarogn': 'https://www.meetup.com/sarogn/',
    'SRCity': 'https://srcity.org/calendar.aspx',
    'iu_jacobs_music': 'https://events.iu.edu/musiciub/',
    'iu_auditorium': 'https://events.iu.edu/iu-auditorium/',
    'iu_eskenazi_museum': 'https://events.iu.edu/artmuseum/',
    'bsquare_government': 'https://bloomington.in.gov/',
    'bsquare_misc_civic': 'https://bsquarebulletin.com/b-there-or-b-square/',
    'bsquare_critical_mass': 'https://bsquarebulletin.com/b-there-or-b-square/',
    'bsquare_bptc': 'https://bloomingtontransit.com/',
    'santa_rosa_arts_center': 'https://santarosaartscenter.org/events/',
    'movingwriting': 'https://www.movingwriting.com/workshops',
    'bigeasy': 'https://bigeasypetaluma.com/events/',
    'polly_klaas': 'https://pollyklaastheater.org/events/',
    'brooksnote': 'https://brooksnotewinery.com/event-calendar/',
    'petaluma_arts_center': 'https://petalumaartscenter.org/events-exhibitions',
    'brewsters': 'https://brewstersbeergarden.com/calendar1',
    'cool_petaluma': 'https://coolpetaluma.org/events',
    'mcnears': 'https://www.mcnears.com/event/',
    'griffo': 'https://griffodistillery.com/pages/calendar',
    'elks_lodge': 'https://elks901.org/calendar-of-events/',
    'garden_club': 'https://petalumagardenclub.org/calendar/',
    'petaluma_bounty': 'https://petalumabounty.org/events-calendar/',
    # Toronto
    'now_toronto': 'https://nowtoronto.com/events/',
    'torevent': 'https://tockify.com/torevent/',
    'jazz_bistro': 'https://jazzbistro.ca/events/',
    'grossmans_tavern': 'https://grossmanstavern.com/events/',
    'union_station': 'https://torontounion.ca/toronto-union-events/',
    'distillery_events': 'https://tockify.com/distilleryevents/',
    'gardiner_museum': 'https://www.gardinermuseum.on.ca/events/',
    'toronto_botanical': 'https://www.torontobotanicalgarden.ca/events/',
    'textile_museum': 'https://www.textilemuseum.ca/events/',
    'bata_shoe_museum': 'https://batashoemuseum.ca/events/',
    'buddies_theatre': 'https://www.buddiesinbadtimes.com/events/',
    'factory_theatre': 'https://www.factorytheatre.ca/events/',
    'high_park_nature': 'https://highparknaturecentre.com/events/',
    'york_university': 'https://events.yorku.ca/',
    'uoft_events': 'https://www.utoronto.ca/events',
    'uoft_engineering': 'https://www.engineering.utoronto.ca/engineering-events/',
    'uoft_philosophy': 'https://philosophy.utoronto.ca/events/',
    'uoft_socialwork': 'https://socialwork.utoronto.ca/events/',
    'culturelink': 'https://www.culturelink.ca/events/',
    'scadding_court': 'https://scaddingcourt.org/events/',
    'st_lawrence_na': 'https://tockify.com/st.lawrence.na/',
    'bloor_west_village': 'https://www.bloorwestvillagebia.com/events/',
    'jamaalmyers': 'https://tockify.com/jamaalmyers/',
    'showup_toronto': 'https://showuptoronto.ca/',
    'meetup_sai_dham_volunteer': 'https://www.meetup.com/sai-dham-canada-toronto-volunteer-group/',
    'meetup_toronto_dads': 'https://www.meetup.com/torontodadsgroup/',
    'meetup_little_sunbeams': 'https://www.meetup.com/little-sunbeams-parents-tots-meetup/',
    'meetup_mini_me': 'https://www.meetup.com/mini-me-meetups/',
    'ontario_nature': 'https://ontarionature.org/events-calendar/',
    'repair_cafe_toronto': 'https://repaircafetoronto.ca/get-our-events-feed/',
    'knitters_guild': 'https://torontoknittersguild.ca/events/',
    'site3': 'https://www.site3.ca/events/',
    'toronto_meetings': 'https://www.toronto.ca/city-government/council/',
    'toronto_festivals': 'https://open.toronto.ca/dataset/festivals-events/',
    'volunteer_toronto': 'https://www.volunteertoronto.ca/networking/events/calendar.asp',
    'tpl_events': 'https://tpl.bibliocommons.com/v2/events',
    'cita_local_events': 'https://www.cita.utoronto.ca/events/event-calendar/',
    'cita_seminars': 'https://www.cita.utoronto.ca/events/event-calendar/',
    'cita_special_events': 'https://www.cita.utoronto.ca/events/event-calendar/',
    # Raleigh-Durham
    'duke_gardens': 'https://gardens.duke.edu/calendar/',
    'durham_chamber': 'https://members.durhamchamber.org/events',
    'wakeforest_chamber': 'https://chambermaster.wakeforestchamber.org/events',
    'apex_chamber': 'https://business.apexchamber.com/events',
    'duke': 'https://calendar.duke.edu/events/',
    'unc_chapel_hill': 'https://calendar.unc.edu/',
    'ncsu': 'https://calendar.ncsu.edu/',
    'nc_cultural_resources': 'https://events.dncr.nc.gov/',
    'durham_library': 'https://durhamcountylibrary.libcal.com/calendar',
    'durham_gov': 'https://www.durhamnc.gov/calendar.aspx',
    # Raleigh-Durham - Squarespace scrapers
    'ponysaurus': 'https://ponysaurusbrewing.com/events',
    'scrap_exchange': 'https://scrapexchange.org/tsecalendar',
    'keep_durham_beautiful': 'https://keepdurhambeautiful.org/events',
    'haw_river_assembly': 'https://hawriver.org/events',
    'durham_resistance_1': 'https://durhamresistance.com/calendar',
    'durham_resistance_2': 'https://durhamresistance.com/calendar',
    'durham_resistance_3': 'https://durhamresistance.com/calendar',
    'durham_resistance_4': 'https://durhamresistance.com/calendar',
    'bike_durham': 'https://bikedurham.org/events',
    'triangle_cycling': 'https://www.trianglecycling.org/',
    'gizmo_brew_works': 'https://gizmobrewworks.com/durham-taproom/',
    'lgbtq_center_durham': 'https://www.lgbtqcenterofdurham.org/',
    'eno_river': 'https://www.enoriver.org/events/',
    'new_hope_bird_alliance': 'https://newhopeaudubon.org/events/',
    'wake_audubon': 'https://www.wakeaudubon.org/events',
    'sw_durham_rotary': 'https://portal.clubrunner.ca/3674',
    'jack_london_park': 'https://jacklondonpark.com/events/',
}


def load_allowed_cities(input_dir):
    """Load allowed and excluded cities from city directory if file exists.
    
    Returns (allowed_cities, excluded_cities) tuple.
    Lines starting with '!' are excluded cities (filtered even without address indicators).
    """
    cities_file = Path(input_dir) / 'allowed_cities.txt'
    if not cities_file.exists():
        return None, None
    
    allowed = set()
    excluded = set()
    for line in cities_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            # Strip trailing comment (e.g., "Petaluma  # 38.23, -122.63 (0.0 mi)")
            city = line.split('#')[0].strip()
            if city.startswith('!'):
                # Excluded city
                excluded.add(city[1:].strip().lower())
            elif city:
                allowed.add(city.lower())
    return allowed if allowed else None, excluded if excluded else None


# Locations that should always be allowed (virtual events, etc.)
VIRTUAL_LOCATION_PATTERNS = [
    'zoom',
    'online',
    'virtual',
    'webinar',
    'http://',
    'https://',
    'america/los_angeles',  # Malformed Meetup timezone-as-location
    'america/new_york',
]

# Patterns that indicate location is a real address (worth geo-filtering)
# If none of these match, we skip geo-filtering for that event
ADDRESS_INDICATORS = re.compile(
    r'(?:'
    r', [A-Z]{2}\b|'              # State abbreviation: ", CA"
    r'\b\d{5}\b|'                 # ZIP code
    r', [A-Z][a-z]+ [A-Z]{2}|'     # City, State: ", Santa Rosa CA"
    r'\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|way|court|ct)\b'  # Street address: "123 Main St"
    r')',
    re.IGNORECASE
)


def location_matches_allowed_cities(location, allowed_cities, excluded_cities=None):
    """Check if a location string contains any allowed city name.
    
    Only applies geo-filter to locations that look like real addresses,
    UNLESS the location contains an explicitly excluded city name.
    Venue-only names ("Theater", "BiblioBus") are allowed through.
    """
    if not allowed_cities:
        return True  # No filter configured
    if not location:
        return True  # No location to check, allow it
    
    location_lower = location.lower()
    
    # Always allow virtual/online events
    for pattern in VIRTUAL_LOCATION_PATTERNS:
        if pattern in location_lower:
            return True
    
    # Check for explicitly excluded cities (even without address indicators)
    if excluded_cities:
        for city in excluded_cities:
            if city in location_lower:
                return False
    
    # Check if location looks like an address
    # If not, allow it through (venue name only, no geo info to filter on)
    if not ADDRESS_INDICATORS.search(location):
        return True
    
    # Location has address info - check against allowed cities
    for city in allowed_cities:
        if city in location_lower:
            return True
    return False


def get_source_name(filename):
    """Get friendly source name from filename."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return 'City of Santa Rosa'
    return SOURCE_NAMES.get(stem, stem.replace('_', ' ').title())


def get_fallback_url(filename):
    """Get fallback URL for a source."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return SOURCE_URLS.get('SRCity')
    return SOURCE_URLS.get(stem)


def parse_ics_datetime(dt_str):
    """Parse an ICS datetime string to a datetime object."""
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]
    
    dt_str = dt_str.strip()
    
    try:
        if dt_str.endswith('Z'):
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        elif 'T' in dt_str:
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
        else:
            return datetime.strptime(dt_str, '%Y%m%d')
    except ValueError:
        return None


def normalize_title(title):
    """Normalize title for dedup matching: strip leading article, lowercase, alphanumeric only, first 40 chars."""
    if not title:
        return ''
    # Strip leading articles ("The", "A", "An") to improve matching
    # e.g. "The Sam Grisman Project" matches "Sam Grisman Project"
    lower = title.lower()
    for article in ('the ', 'a ', 'an '):
        if lower.startswith(article):
            title = title[len(article):]
            break
    return ''.join(c.lower() for c in title if c.isalnum())[:40]


def extract_field(event_content, field_name):
    """Extract a field value from VEVENT content, handling line folding."""
    # Match field, handling continuation lines (start with space/tab)
    # Use (?:;[^:]*)?  to allow ICS parameters (e.g. DTSTART;TZID=...:value)
    # but prevent matching longer field names (e.g. X-SOURCE-ID when searching for X-SOURCE)
    pattern = rf'^{field_name}(?:;[^:]*)?:([^\r\n]+(?:[\r\n]+[ \t][^\r\n]+)*)'
    match = re.search(pattern, event_content, re.MULTILINE | re.IGNORECASE)
    if match:
        # Unfold: remove newline+space/tab
        value = re.sub(r'[\r\n]+[ \t]', '', match.group(1))
        # Unescape ICS escapes
        value = value.replace('\\n', ' ').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
        return value.strip()
    return None


def get_dedup_key(event):
    """Generate dedup key from event: (date, normalized_title)."""
    date_str = event['dtstart'].strftime('%Y-%m-%d')
    title = extract_field(event['content'], 'SUMMARY') or ''
    return (date_str, normalize_title(title))


# Known aggregators - these get lowest priority in deduplication.
# When the same event appears in an aggregator AND a primary source,
# we keep the primary source version.
AGGREGATORS = {
    'North Bay Bohemian',
    'Press Democrat',
    'Creative Sonoma',
    'GoLocal Cooperative',
    'NOW Toronto',
    'Toronto Events (Tockify)',
}


def is_aggregator(source_name):
    """Check if a source is a known aggregator (low priority for dedup)."""
    return source_name in AGGREGATORS


def dedupe_cross_source(events, input_dir):
    """Deduplicate events across sources using title+date matching.

    When duplicates are found, prefers primary sources over aggregators.
    Among primary sources or among aggregators, keeps the first encountered.
    Also merges groups where one title is a prefix of another on the same date
    (handles aggregators that append "at Venue Name" to titles).
    """
    # Group events by dedup key
    groups = {}
    for event in events:
        key = get_dedup_key(event)
        if key not in groups:
            groups[key] = []
        groups[key].append(event)

    # Second pass: merge groups where one normalized title is a prefix of another
    # on the same date. This handles "Hands on a Hardbody" vs
    # "Hands on a Hardbody at Spreckels Performing Arts Center".
    # Only merge if the shorter title is at least 12 chars (avoid false positives).
    date_keys = {}
    for key in groups:
        date_str, norm_title = key
        if date_str not in date_keys:
            date_keys[date_str] = []
        date_keys[date_str].append(key)

    merged_into = {}  # key -> canonical key it was merged into
    for date_str, keys in date_keys.items():
        if len(keys) < 2:
            continue
        # Sort by title length so shorter titles come first
        keys.sort(key=lambda k: len(k[1]))
        for i in range(len(keys)):
            if keys[i] in merged_into:
                continue
            short_title = keys[i][1]
            if len(short_title) < 12:
                continue
            for j in range(i + 1, len(keys)):
                if keys[j] in merged_into:
                    continue
                long_title = keys[j][1]
                if long_title.startswith(short_title) and len(short_title) / len(long_title) <= 0.75:
                    # Only merge if at least one group contains an aggregator event.
                    # This avoids merging unrelated events that happen to share a prefix
                    # (e.g. "After School Club" vs "After School Club Robotics" at different libraries).
                    has_aggregator = False
                    for e in groups[keys[i]] + groups[keys[j]]:
                        src = extract_field(e['content'], 'X-SOURCE') or ''
                        if any(is_aggregator(s.strip()) for s in src.split(',')):
                            has_aggregator = True
                            break
                    if not has_aggregator:
                        continue
                    # Merge longer-title group into shorter-title group
                    groups[keys[i]].extend(groups[keys[j]])
                    merged_into[keys[j]] = keys[i]
                    print(f"  Prefix dedup: merged '{keys[j][1][:50]}' into '{keys[i][1][:50]}' on {date_str}")

    # Remove merged groups
    for key in merged_into:
        del groups[key]

    # For each group, keep primary source over aggregator
    unique_events = []
    cross_source_deduped = 0

    for key, group in groups.items():
        if len(group) == 1:
            unique_events.append(group[0])
        else:
            # Multiple events with same title+date
            # Sort: primary sources first, aggregators last
            group.sort(key=lambda e: (1 if is_aggregator(extract_field(e['content'], 'X-SOURCE') or '') else 0))
            
            # Merge sources from all duplicates into the kept event
            kept = group[0]
            all_sources = []
            source_urls = {}
            for e in group:
                src = extract_field(e['content'], 'X-SOURCE')
                evt_url = extract_field(e['content'], 'URL')
                if src:
                    for s in src.split(','):
                        s = s.strip()
                        if s and s not in all_sources:
                            all_sources.append(s)
                        if s and evt_url:
                            source_urls[s] = evt_url

            # Update X-SOURCE to combined value
            if len(all_sources) > 1:
                merged_source = ', '.join(sorted(all_sources))
                kept['content'] = re.sub(
                    r'^X-SOURCE:[^\r\n]+',
                    f'X-SOURCE:{merged_source}',
                    kept['content'],
                    flags=re.MULTILINE
                )

            # Store per-source URLs for aggregator attribution
            if source_urls:
                kept['content'] = f'X-SOURCE-URLS:{json.dumps(source_urls)}\r\n{kept["content"]}'

            unique_events.append(kept)
            cross_source_deduped += len(group) - 1
    
    if cross_source_deduped > 0:
        print(f"  Cross-source dedup: removed {cross_source_deduped} duplicate events")
    
    # Re-sort by start time
    unique_events.sort(key=lambda x: x['dtstart'].replace(tzinfo=timezone.utc) if x['dtstart'].tzinfo is None else x['dtstart'])
    
    return unique_events


def dedupe_fuzzy(events, input_dir):
    """Use LLM to find duplicates with different titles.
    
    Groups events by date, asks Claude to cluster same-events,
    then keeps highest-priority source from each cluster.
    Logs matches to {input_dir}/fuzzy_dedup.log for analysis.
    """
    import os
    from datetime import datetime
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("  Fuzzy dedup: ANTHROPIC_API_KEY not set, skipping")
        return events
    
    try:
        import anthropic
    except ImportError:
        print("  Fuzzy dedup: anthropic package not installed, skipping")
        return events
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Open log file
    log_path = Path(input_dir) / 'fuzzy_dedup.log'
    log_file = open(log_path, 'w')  
    log_file.write(f"Fuzzy dedup run: {datetime.now().isoformat()}\n")
    log_file.write(f"Total events: {len(events)}\n\n")
    
    # Group by date
    by_date = {}
    for event in events:
        date_str = event['dtstart'].strftime('%Y-%m-%d')
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(event)
    
    # Track which events to remove (by index in original list)
    events_to_remove = set()
    fuzzy_deduped = 0
    api_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    dates_with_multiple = 0

    
    for date_str, day_events in by_date.items():
        if len(day_events) < 2:
            continue
        
        dates_with_multiple += 1
        
        # Build prompt with event summaries
        event_lines = []
        for i, e in enumerate(day_events):
            title = extract_field(e['content'], 'SUMMARY') or '(no title)'
            source = extract_field(e['content'], 'X-SOURCE') or 'Unknown'
            location = extract_field(e['content'], 'LOCATION') or ''
            time_str = e['dtstart'].strftime('%H:%M')
            loc_part = f", {location}" if location else ""
            event_lines.append(f"{i+1}. {title} ({source}, {time_str}{loc_part})")
        
        log_file.write(f"CHECKING: {date_str} ({len(event_lines)} events)\n")
        
        prompt = f"""Events on {date_str}. Group any that are the SAME event (same actual gathering, possibly with different titles).

{chr(10).join(event_lines)}

Respond with ONLY a JSON array of arrays grouping indices of same events.
Example: [[1,2], [3], [4,5,6]] means 1&2 are same event, 3 is unique, 4&5&6 are same event.
If all events are unique, respond: [[1], [2], [3], ...]

JSON:"""
        
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track API usage
            api_calls += 1
            if hasattr(response, 'usage'):
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
            
            # Parse response
            import json
            text = response.content[0].text.strip()
            # Handle markdown code blocks
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('\n', 1)[0]
            clusters = json.loads(text)
            
            # Process clusters - keep highest priority from each
            for cluster in clusters:
                if len(cluster) <= 1:
                    continue
                
                # Get events in this cluster (convert 1-indexed to 0-indexed)
                cluster_events = [(idx-1, day_events[idx-1]) for idx in cluster if 0 < idx <= len(day_events)]
                if len(cluster_events) <= 1:
                    continue
                
                # Sort by priority (non-aggregators first)
                cluster_events.sort(key=lambda x: (1 if is_aggregator(extract_field(x[1]['content'], 'X-SOURCE') or '') else 0))
                
                # Keep first, merge sources from rest, then mark rest for removal
                kept_idx, kept_event = cluster_events[0]
                kept_title = extract_field(kept_event['content'], 'SUMMARY') or '(no title)'
                kept_source = extract_field(kept_event['content'], 'X-SOURCE') or 'Unknown'
                
                # Collect all sources and their URLs for merging
                all_sources = []
                source_urls = {}
                if kept_source != 'Unknown':
                    all_sources.extend(s.strip() for s in kept_source.split(','))
                kept_url = extract_field(kept_event['content'], 'URL')
                if kept_source != 'Unknown' and kept_url:
                    source_urls[kept_source] = kept_url

                for idx, removed_event in cluster_events[1:]:
                    removed_title = extract_field(removed_event['content'], 'SUMMARY') or '(no title)'
                    removed_source = extract_field(removed_event['content'], 'X-SOURCE') or 'Unknown'
                    removed_url = extract_field(removed_event['content'], 'URL')

                    if removed_source != 'Unknown':
                        for s in removed_source.split(','):
                            s = s.strip()
                            if s and s not in all_sources:
                                all_sources.append(s)
                            if s and removed_url:
                                source_urls[s] = removed_url

                    match_line = f"[{date_str}] '{removed_title}' ({removed_source}) -> '{kept_title}' ({kept_source})"
                    print(f"    Fuzzy match: {match_line}")
                    log_file.write(f"MATCH: {match_line}\n")

                    # Find this event in the original list
                    orig_idx = events.index(day_events[idx])
                    events_to_remove.add(orig_idx)
                    fuzzy_deduped += 1

                # Merge sources into kept event
                if len(all_sources) > 1:
                    merged_source = ', '.join(sorted(all_sources))
                    kept_event['content'] = re.sub(
                        r'^X-SOURCE:[^\r\n]+',
                        f'X-SOURCE:{merged_source}',
                        kept_event['content'],
                        flags=re.MULTILINE
                    )
                    log_file.write(f"  -> Merged sources: {merged_source}\n")

                # Store per-source URLs for aggregator attribution
                if source_urls:
                    kept_event['content'] = f'X-SOURCE-URLS:{json.dumps(source_urls)}\r\n{kept_event["content"]}'
                    
        except Exception as e:
            error_msg = f"ERROR [{date_str}]: {e}"
            print(f"  Fuzzy dedup: {error_msg}")
            log_file.write(f"{error_msg}\n")
            # Log the raw response if available for debugging
            if 'text' in dir():
                log_file.write(f"  Raw response: {text[:500]}\n")
            continue
    
    # Write summary and close log file
    log_file.write(f"\n--- Summary ---\n")
    log_file.write(f"Dates with 2+ events: {dates_with_multiple}\n")

    log_file.write(f"API calls made: {api_calls}\n")
    log_file.write(f"Total input tokens: {total_input_tokens}\n")
    log_file.write(f"Total output tokens: {total_output_tokens}\n")
    log_file.write(f"Fuzzy matches found: {fuzzy_deduped}\n")
    log_file.close()
    
    print(f"  Fuzzy dedup: {api_calls} API calls, {total_input_tokens}+{total_output_tokens} tokens")
    
    if fuzzy_deduped > 0:
        print(f"  Fuzzy dedup: removed {fuzzy_deduped} duplicate events (see fuzzy_dedup.log)")
    else:
        print(f"  Fuzzy dedup: no additional duplicates found")
    
    # Return events with duplicates removed
    return [e for i, e in enumerate(events) if i not in events_to_remove]


def extract_events(ics_content, source_name=None, source_id=None, fallback_url=None):
    """Extract VEVENT blocks from ICS content."""
    events = []

    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, ics_content, re.DOTALL)

    for event_content in matches:
        dtstart_match = re.search(r'DTSTART[^:]*:([^\r\n]+)', event_content)
        if dtstart_match:
            dt = parse_ics_datetime(dtstart_match.group(1))
            if dt:
                # Add fallback URL if no URL exists
                if fallback_url and 'URL:' not in event_content:
                    event_content = f'URL:{fallback_url}\r\n{event_content}'

                # Add X-SOURCE, X-SOURCE-ID, and X-SOURCE-URLS headers
                # (source attribution is rendered by the app from X-SOURCE)
                if source_name:
                    if 'X-SOURCE' not in event_content:
                        event_content = f'X-SOURCE:{source_name}\r\n{event_content}'
                    if source_id and 'X-SOURCE-ID' not in event_content:
                        event_content = f'X-SOURCE-ID:{source_id}\r\n{event_content}'
                    # Build initial source_urls mapping so every event has one,
                    # not just events that go through dedup merging
                    evt_url = extract_field(event_content, 'URL')
                    if evt_url and 'X-SOURCE-URLS' not in event_content:
                        event_content = f'X-SOURCE-URLS:{json.dumps({source_name: evt_url})}\r\n{event_content}'
                
                events.append({
                    'dtstart': dt,
                    'content': event_content
                })
    
    return events


def combine_ics_files(input_dir, output_file, calendar_name="Combined Calendar", exclude_sources=None):
    """Combine all ICS files in a directory into one.
    
    Args:
        exclude_sources: Set of source filenames (without .ics) to skip
    """
    all_events = []
    geo_filtered_count = 0
    exclude_sources = exclude_sources or set()
    # Use 24 hours ago to avoid filtering out same-day events due to timezone differences
    from datetime import timedelta
    now = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Load allowed cities for geo filtering
    allowed_cities, excluded_cities = load_allowed_cities(input_dir)
    if allowed_cities:
        print(f"  Geo filter active: {len(allowed_cities)} allowed cities")
    if excluded_cities:
        print(f"  Excluded cities: {len(excluded_cities)}")
    
    ics_dir = Path(input_dir)
    for ics_file in sorted(ics_dir.glob('*.ics')):
        # Skip output files (combined.ics or the specified output)
        if ics_file.name == Path(output_file).name or ics_file.stem == 'combined':
            continue
        
        # Skip excluded sources
        if ics_file.stem in exclude_sources:
            print(f"  SKIP {ics_file.name} (excluded)")
            continue
            
        try:
            content = ics_file.read_text(encoding='utf-8', errors='ignore')
            source_name = get_source_name(ics_file.name)
            source_id = ics_file.stem  # filename without .ics
            fallback_url = get_fallback_url(ics_file.name)
            events = extract_events(content, source_name, source_id, fallback_url)
            
            # Filter to future events only
            future_events = [e for e in events if e['dtstart'].replace(tzinfo=timezone.utc) >= now]
            
            # Apply geo filter if configured
            if allowed_cities:
                filtered_events = []
                for e in future_events:
                    # Handle ICS line folding (continuation lines start with space/tab)
                    # Use ^LOCATION to avoid matching X-LIC-LOCATION
                    location_match = re.search(r'^LOCATION:([^\n]+(?:\n[ \t][^\n]+)*)', e['content'], re.MULTILINE)
                    if location_match:
                        # Unfold: remove newline+space/tab
                        location = re.sub(r'\n[ \t]', '', location_match.group(1))
                    else:
                        location = ''
                    if location_matches_allowed_cities(location, allowed_cities, excluded_cities):
                        filtered_events.append(e)
                    else:
                        geo_filtered_count += 1
                future_events = filtered_events
            
            all_events.extend(future_events)
            
            if future_events:
                print(f"  {len(future_events):4d} future events from {ics_file.name} ({source_name})")
        except Exception as e:
            print(f"  Error processing {ics_file.name}: {e}")
    
    # Sort by start time
    def normalize_dt(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    all_events.sort(key=lambda x: normalize_dt(x['dtstart']))
    
    # Remove duplicates based on UID (same-source duplicates)
    seen_uids = set()
    uid_deduped = []
    for event in all_events:
        uid_match = re.search(r'UID:([^\r\n]+)', event['content'])
        if uid_match:
            uid = uid_match.group(1)
            if uid not in seen_uids:
                seen_uids.add(uid)
                uid_deduped.append(event)
        else:
            uid_deduped.append(event)
    
    # Cross-source deduplication: group by (date, normalized_title)
    # Keep the event from the highest-priority source (primary sources over aggregators)
    unique_events = dedupe_cross_source(uid_deduped, input_dir)
    
    # Fuzzy deduplication: use LLM to find duplicates with different titles
    import os
    if os.environ.get('ENABLE_FUZZY_DEDUP'):
        unique_events = dedupe_fuzzy(unique_events, input_dir)
    
    # Build combined ICS
    output = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Combined Feed//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{calendar_name}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT1H',
        'X-PUBLISHED-TTL:PT1H',
    ]
    
    for event in unique_events:
        output.append('BEGIN:VEVENT')
        output.append(event['content'])
        output.append('END:VEVENT')
    
    output.append('END:VCALENDAR')
    
    Path(output_file).write_text('\r\n'.join(output), encoding='utf-8')
    
    if geo_filtered_count > 0:
        print(f"  (Geo-filtered {geo_filtered_count} events outside allowed cities)")
    print(f"\nCombined {len(unique_events)} unique future events into {output_file}")
    return len(unique_events)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine ICS files into a single feed')
    parser.add_argument('--input-dir', '-i', required=True, help='Directory containing ICS files')
    parser.add_argument('--output', '-o', required=True, help='Output ICS file')
    parser.add_argument('--name', '-n', default='Community Calendar', help='Calendar name')
    parser.add_argument('--exclude', '-x', default='', help='Comma-separated source filenames to exclude (without .ics)')
    
    args = parser.parse_args()
    exclude_sources = set(s.strip() for s in args.exclude.split(',') if s.strip())
    
    print(f"Combining ICS files from {args.input_dir}...")
    if exclude_sources:
        print(f"  Excluding sources: {', '.join(sorted(exclude_sources))}")
    combine_ics_files(args.input_dir, args.output, args.name, exclude_sources)
