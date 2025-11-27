from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class ConversationMemory:
    
    def __init__(self):
        # Keep track of what users are talking about right now
        self.short_term_memory = {}
        # Remember what users like across different chats to give better suggestions
        self.long_term_memory = {}
        
    def update_context(self, conversation_id: str, key: str, value: Any):
        # Update what we remember about this conversation.
        if conversation_id not in self.short_term_memory:
            self.short_term_memory[conversation_id] = {}

    def store_context(self, conversation_id: str, context: Any, insights: dict = None) -> bool:
        # Remember what the user said so we can keep the conversation flowing naturally.
        # We handle different types of information (like destinations, budgets, dates)
        # and keep track of how often things are mentioned so we can give better
        # travel suggestions that feel personalized.
        # Set up memory for this conversation if it's new
        if conversation_id not in self.short_term_memory:
            self.short_term_memory[conversation_id] = {}
        
        # Figure out what kind of information we're storing
        if isinstance(context, dict):
            # Store each piece of info separately (destinations, budget, dates, etc.)
            for key, value in context.items():
                self.short_term_memory[conversation_id][key] = {
                    "value": value,
                    "timestamp": datetime.now(timezone.utc),
                    "mentioned_count": self.short_term_memory[conversation_id].get(key, {}).get("mentioned_count", 0) + 1
                }
        elif isinstance(context, list):
            # Store the whole conversation history
            self.short_term_memory[conversation_id]["messages"] = {
                "value": context,
                "timestamp": datetime.now(timezone.utc),
                "mentioned_count": self.short_term_memory[conversation_id].get("messages", {}).get("mentioned_count", 0) + 1
            }
        else:
            # Store any other vacation planning info
            self.short_term_memory[conversation_id]["context"] = {
                "value": context,
                "timestamp": datetime.now(timezone.utc),
                "mentioned_count": self.short_term_memory[conversation_id].get("context", {}).get("mentioned_count", 0) + 1
            }
        
        # Also remember any smart insights we figured out
        if insights:
            for key, value in insights.items():
                self.short_term_memory[conversation_id][f"insight_{key}"] = {
                    "value": value,
                    "timestamp": datetime.now(timezone.utc),
                    "mentioned_count": 1
                }
        
        return True
    
    def get_context(self, conversation_id: str) -> Dict:
        # Get what we remember about this conversation, focusing on the most relevant information
        if conversation_id not in self.short_term_memory:
            return {}
        
        context = {}
        current_time = datetime.now(timezone.utc)
        
        for key, data in self.short_term_memory[conversation_id].items():
            # Calculate relevance score for this information
            time_diff = (current_time - data["timestamp"]).seconds
            recency_score = max(0, 1 - (time_diff / 3600))  # Less important as time passes
            frequency_score = min(1, data["mentioned_count"] / 5)  # More important if mentioned often
            
            relevance = (recency_score * 0.7) + (frequency_score * 0.3)
            
            if relevance > 0.3:  # Only keep the stuff that's still relevant
                context[key] = {
                    "value": data["value"],
                    "relevance": relevance
                }
        
        return context
    
    def extract_key_points(self, messages: List[Dict]) -> Dict:
        # Extract key information from user messages about their vacation
        key_points = {
            "destinations": [],
            "requirements": [],
            "preferences": [],
            "concerns": [],
            "decisions_made": []
        }
        
        # Places people commonly talk about when planning trips
        destinations = [
            "paris", "nice", "lyon", "marseille", "bordeaux", "toulouse", "cannes", 
            "versailles", "madrid", "barcelona", "seville", "valencia", "granada", 
            "bilbao", "malaga", "palma de mallorca", "rome", "milan", "florence", 
            "venice", "naples", "palermo", "catania", "amalfi coast", "london", 
            "edinburgh", "manchester", "bath", "oxford", "york", "cambridge", 
            "liverpool", "berlin", "munich", "frankfurt", "cologne", "hamburg", 
            "dresden", "dusseldorf", "amsterdam", "rotterdam", "utrecht", "hague", 
            "leiden", "vienna", "salzburg", "innsbruck", "graz", "prague", "brno", 
            "cesky krumlov", "budapest", "szeged", "debrecen", "athens", 
            "santorini", "mykonos", "thessaloniki", "crete", "rhodes", "corfu", 
            "istanbul", "cappadocia", "antalya", "izmir", "ankara", "pamukkale", 
            "moscow", "saint petersburg", "kazan", "yekaterinburg", "novosibirsk", 
            "new york", "los angeles", "chicago", "miami", "san francisco", "dallas", 
            "orlando", "washington dc", "toronto", "montreal", "vancouver", "calgary", 
            "ottawa", "quebec city", "mexico city", "cancun", "guadalajara", 
            "puerto vallarta", "merida", "san miguel de allende", "rio de janeiro", 
            "sao paulo", "salvador", "brasilia", "recife", "porto alegre", 
            "buenos aires", "cordoba", "mendoza", "bariloche", "rosario", "lima", 
            "cusco", "machu picchu", "arequipa", "trujillo", "santiago", 
            "valparaiso", "punta arenas", "easter island", "bogota", "medellin", 
            "cali", "cartagena", "santa marta", "cairo", "giza", "alexandria", 
            "luxor", "aswan", "sharm el sheikh", "dubai", "abu dhabi", 
            "ras al khaimah", "delhi", "mumbai", "bangalore", "chennai", "kolkata", 
            "hyderabad", "jaipur", "varanasi", "goa", "beijing", "shanghai", 
            "guangzhou", "shenzhen", "xian", "hong kong", "macau", "hangzhou", 
            "tokyo", "osaka", "kyoto", "yokohama", "sapporo", "fukuoka", "seoul", 
            "busan", "incheon", "daegu", "jeju island", "bangkok", "chiang mai", 
            "phuket", "pattaya", "krabi", "koh samui", "ho chi minh city", "hanoi", 
            "da nang", "hoi an", "nha trang", "hue", "jakarta", "bali", 
            "yogyakarta", "surabaya", "lombok", "bandung", "manila", "cebu", 
            "davao", "palawan", "boracay", "bohol", "kuala lumpur", "penang", 
            "malacca", "langkawi", "kota kinabalu", "sarawak", "sydney", 
            "melbourne", "brisbane", "perth", "adelaide", "gold coast", "auckland", 
            "wellington", "christchurch", "queenstown", "rotorua", "cape town", 
            "johannesburg", "durban", "pretoria", "marrakech", "fes", "casablanca", 
            "chefchaouen", "lisbon", "porto", "sintra", "coimbra", "faro", "riyadh", 
            "jeddah", "medina", "mecca", "afghanistan", "albania", "algeria", 
            "andorra", "angola", "antigua and barbuda", "argentina", "armenia", 
            "australia", "austria", "azerbaijan", "bahamas", "bahrain", 
            "bangladesh", "barbados", "belarus", "belgium", "belize", "benin", 
            "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil", 
            "brunei", "bulgaria", "burkina faso", "burundi", "cabo verde", 
            "cambodia", "cameroon", "canada", "central african republic", "chad", 
            "chile", "china", "colombia", "comoros", "congo", "costa rica", 
            "croatia", "cuba", "cyprus", "czech republic", "denmark", "djibouti", 
            "dominica", "dominican republic", "ecuador", "egypt", "el salvador", 
            "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia", 
            "fiji", "finland", "france", "gabon", "gambia", "georgia", "germany", 
            "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau", 
            "guyana", "haiti", "honduras", "hungary", "iceland", "india", 
            "indonesia", "iran", "iraq", "ireland", "israel", "italy", "jamaica", 
            "japan", "jordan", "kazakhstan", "kenya", "kiribati", "kuwait", 
            "kyrgyzstan", "laos", "latvia", "lebanon", "lesotho", "liberia", 
            "libya", "liechtenstein", "lithuania", "luxembourg", "madagascar", 
            "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands", 
            "mauritania", "mauritius", "mexico", "micronesia", "moldova", "monaco", 
            "mongolia", "montenegro", "morocco", "mozambique", "myanmar", "namibia", 
            "nauru", "nepal", "netherlands", "new zealand", "nicaragua", "niger", 
            "nigeria", "north korea", "north macedonia", "norway", "oman", 
            "pakistan", "palau", "panama", "papua new guinea", "paraguay", "peru", 
            "philippines", "poland", "portugal", "qatar", "romania", "russia", 
            "rwanda", "saint kitts and nevis", "saint lucia", 
            "saint vincent and the grenadines", "samoa", "san marino", 
            "sao tome and principe", "saudi arabia", "senegal", "serbia", 
            "seychelles", "sierra leone", "singapore", "slovakia", "slovenia", 
            "solomon islands", "somalia", "south africa", "south korea", 
            "south sudan", "spain", "sri lanka", "sudan", "suriname", "sweden", 
            "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand", 
            "timor-leste", "togo", "tonga", "trinidad and tobago", "tunisia", 
            "turkey", "turkmenistan", "tuvalu", "uganda", "ukraine", 
            "united arab emirates", "united kingdom", "united states", "uruguay", 
            "uzbekistan", "vanuatu", "venezuela", "vietnam", "yemen", "zambia", 
            "zimbabwe"
        ]
        
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"].lower()
                
                # Look for places they mentioned
                for dest in destinations:
                    if dest in content:
                        # Keep the original spelling/capitalization
                        original_content = msg["content"]
                        if dest in original_content.lower():
                            # Find exactly how they wrote the destination name
                            start_idx = original_content.lower().find(dest)
                            end_idx = start_idx + len(dest)
                            actual_dest = original_content[start_idx:end_idx]
                            if actual_dest not in key_points["destinations"]:
                                key_points["destinations"].append(actual_dest)
                
                # Look for things they said they need or require
                if any(word in content for word in ["need", "must", "require", "important"]):
                    key_points["requirements"].append(msg["content"])
                
                # Look for things they said they like or want
                if any(word in content for word in ["prefer", "like", "love", "want"]):
                    key_points["preferences"].append(msg["content"])
                
                # Look for decisions they've made
                if any(word in content for word in ["decided", "going to", "will", "booked"]):
                    key_points["decisions_made"].append(msg["content"])
                
                # Look for things they're worried about
                if any(word in content for word in ["worried", "concerned", "afraid", "scared", "nervous"]):
                    key_points["concerns"].append(msg["content"])
        
        return key_points
    
    def clear_context(self, conversation_id: str):
        # Forget everything about this specific conversation.
        if conversation_id in self.short_term_memory:
            # Wipe out all memories of this chat
            del self.short_term_memory[conversation_id]
    
    def cleanup_old_contexts(self, max_age_hours: int = 24):
        # Clean up old conversation memories to keep things tidy.
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        conversations_to_remove = []
        
        for conversation_id, context in self.short_term_memory.items():
            # Check if everything in this conversation is old
            all_old = all(
                data["timestamp"] < cutoff_time 
                for data in context.values()
            )
            
            if all_old:
                conversations_to_remove.append(conversation_id)
        
        # Remove the old conversations
        for conversation_id in conversations_to_remove:
            del self.short_term_memory[conversation_id]
        
        if conversations_to_remove:
            logger.info(f"Cleaned up {len(conversations_to_remove)} old conversation memories")