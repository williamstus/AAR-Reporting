#!/usr/bin/env python3
"""
Corrected Fort Moore Training Exercise Data Simulator
Proper Military Structure: 2 Platoons × 4 Squads × 7 Soldiers = 56 Total Callsigns

Exercise Timeline:
- Movement Phase: 1 hour (120 reports per callsign)
- Engagement Phase: 30 minutes (60 reports per callsign)
- Total: 90 minutes × 56 soldiers = 10,080 total position reports
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import math

class CorrectedFortMooreSimulator:
    def __init__(self):
        # Exercise area coordinates (from Fort Moore image)
        self.exercise_bounds = {
            'min_lat': 32.3825,
            'max_lat': 32.3875,
            'min_lon': -84.9975,
            'max_lon': -84.9925
        }
        
        # Key locations from the exercise area
        self.locations = {
            'residential_compound': {'lat': 32.3845, 'lon': -84.9950},
            'generals_field': {'lat': 32.3850, 'lon': -84.9935},
            'blackhawk_trail': {'lat': 32.3840, 'lon': -84.9945},
            'mckenna_tower': {'lat': 32.3830, 'lon': -84.9960},
            'baughman_field': {'lat': 32.3855, 'lon': -84.9930}
        }
        
        # 802.11ah Mesh Access Points for network coverage
        self.mesh_aps = [
            {'id': 'MAP_001', 'lat': 32.3845, 'lon': -84.9950, 'power': 37},  # Residential (5W + 9dBi = 37dBm EIRP)
            {'id': 'MAP_002', 'lat': 32.3850, 'lon': -84.9935, 'power': 37},  # General's Field
            {'id': 'MAP_003', 'lat': 32.3840, 'lon': -84.9945, 'power': 37},  # Blackhawk Trail
            {'id': 'MAP_004', 'lat': 32.3835, 'lon': -84.9940, 'power': 37},  # Central Coverage
            {'id': 'MAP_005', 'lat': 32.3855, 'lon': -84.9930, 'power': 37},  # Baughman Field
            {'id': 'MAP_006', 'lat': 32.3830, 'lon': -84.9955, 'power': 37},  # McKenna Tower Area
        ]
        
        # Corrected Exercise Timeline
        self.movement_duration_minutes = 60    # 1 hour movement
        self.engagement_duration_minutes = 30  # 30 minutes engagement
        self.total_duration_minutes = 90       # Total: 1.5 hours
        self.sample_interval_seconds = 30      # Report every 30 seconds
        
        # Calculate total samples
        self.total_samples = int((self.total_duration_minutes * 60) / self.sample_interval_seconds)  # 180 samples
        self.movement_samples = int((self.movement_duration_minutes * 60) / self.sample_interval_seconds)  # 120 samples
        
        print(f"Exercise Parameters:")
        print(f"- Total Duration: {self.total_duration_minutes} minutes")
        print(f"- Movement Phase: {self.movement_duration_minutes} minutes ({self.movement_samples} samples)")
        print(f"- Engagement Phase: {self.engagement_duration_minutes} minutes ({self.total_samples - self.movement_samples} samples)")
        print(f"- Sample Interval: {self.sample_interval_seconds} seconds")
        print(f"- Total Samples per Soldier: {self.total_samples}")
        
        # Corrected Platoon Structure: 2 Platoons × 4 Squads × 7 Soldiers = 56 Total
        self.platoons = {
            'BLUE_FORCE': {
                'squads': ['ALPHA', 'BRAVO', 'CHARLIE', 'DELTA'],
                'start_location': 'residential_compound',
                'objective': 'generals_field',
                'callsign_prefix': 'BLUE'
            },
            'OPFOR': {
                'squads': ['ECHO', 'FOXTROT', 'GOLF', 'HOTEL'], 
                'start_location': 'generals_field',
                'objective': 'residential_compound',
                'callsign_prefix': 'RED'
            }
        }
        
        # Generate proper soldier roster with unique callsigns
        self.soldiers = self.generate_corrected_soldier_roster()
        
        # Exercise start time
        self.start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        print(f"Total Soldiers Generated: {len(self.soldiers)}")
        print(f"Expected Total Records: {len(self.soldiers)} × {self.total_samples} = {len(self.soldiers) * self.total_samples:,}")
        
    def generate_corrected_soldier_roster(self):
        """Generate proper military roster: 2 Platoons × 4 Squads × 7 Soldiers = 56 Total"""
        soldiers = []
        
        # Military roles for 7-person squad
        squad_roles = [
            'Squad Leader',      # 1
            'Team Leader Alpha', # 2
            'Rifleman',         # 3
            'Automatic Rifleman', # 4
            'Team Leader Bravo', # 5
            'Grenadier',        # 6
            'Medic'             # 7
        ]
        
        for platoon_name, platoon_data in self.platoons.items():
            callsign_prefix = platoon_data['callsign_prefix']
            
            for squad_idx, squad_name in enumerate(platoon_data['squads'], 1):
                for soldier_idx, role in enumerate(squad_roles, 1):
                    # Generate unique callsign: BLUE_1_1, BLUE_1_2, etc.
                    callsign = f"{callsign_prefix}_{squad_idx}_{soldier_idx}"
                    
                    soldier = {
                        'callsign': callsign,
                        'unit_id': callsign,  # Keep for compatibility
                        'platoon': platoon_name,
                        'squad': f"{callsign_prefix}_{squad_name}",
                        'squad_number': squad_idx,
                        'position_in_squad': soldier_idx,
                        'role': role,
                        'is_squad_leader': (soldier_idx == 1),
                        'is_team_leader': role.startswith('Team Leader')
                    }
                    soldiers.append(soldier)
        
        # Print roster summary
        print(f"\n📋 Generated Military Roster:")
        for platoon_name in self.platoons.keys():
            platoon_soldiers = [s for s in soldiers if s['platoon'] == platoon_name]
            print(f"  {platoon_name}: {len(platoon_soldiers)} soldiers")
            
            # Show squads
            for squad_num in range(1, 5):
                squad_soldiers = [s for s in platoon_soldiers if s['squad_number'] == squad_num]
                squad_callsigns = [s['callsign'] for s in squad_soldiers]
                print(f"    Squad {squad_num}: {squad_callsigns}")
        
        return soldiers
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_rssi_802_11ah(self, soldier_lat, soldier_lon, map_lat, map_lon):
        """Calculate RSSI for 802.11ah at 900MHz in dense forest"""
        distance = max(self.calculate_distance(soldier_lat, soldier_lon, map_lat, map_lon), 1)
        
        # 802.11ah path loss model at 900MHz
        # Free Space Path Loss: FSPL = 20*log10(d) + 20*log10(f) + 32.45
        fspl = 20 * math.log10(distance) + 20 * math.log10(900) + 32.45
        
        # Dense forest attenuation (Georgia pine forest)
        # Severe attenuation at 900MHz in dense vegetation
        forest_loss = min(distance * 1.2, 30)  # Up to 30dB loss in dense forest
        
        # Terrain and multipath effects
        terrain_variation = random.uniform(-8, 8)
        
        # Link budget calculation
        # MAP: 5W (37dBm) + 9dBi antenna = 46dBm EIRP
        # Soldier: 3dBi antenna gain
        tx_eirp = 46  # MAP EIRP
        rx_gain = 3   # Soldier antenna gain
        
        # Calculate received signal strength
        rssi = tx_eirp + rx_gain - fspl - forest_loss + terrain_variation
        
        # Ensure realistic RSSI bounds for 802.11ah
        return max(min(rssi, -10), -95)
    
    def get_squad_formation_position(self, squad_leader_lat, squad_leader_lon, position_in_squad, time_step):
        """Calculate soldier position within tactical squad formation"""
        if position_in_squad == 1:  # Squad leader
            return squad_leader_lat, squad_leader_lon
        
        # Tactical formation spacing (~15-25 meters between soldiers)
        formation_spread = 0.0002  # Approximately 20-25 meters in lat/lon
        
        # Formation pattern: modified wedge
        if position_in_squad <= 4:  # Alpha team
            team_angle = -45  # Left side of squad leader
            team_position = position_in_squad - 1
        else:  # Bravo team
            team_angle = 45   # Right side of squad leader
            team_position = position_in_squad - 4
        
        # Calculate position within team
        angle_rad = math.radians(team_angle + (team_position * 15))
        distance = formation_spread * (0.8 + team_position * 0.3)
        
        # Add tactical movement variation
        movement_variation = 0.00003 * math.sin(time_step * 0.08 + position_in_squad)
        
        lat_offset = distance * math.cos(angle_rad) + movement_variation
        lon_offset = distance * math.sin(angle_rad) + movement_variation * 0.7
        
        return squad_leader_lat + lat_offset, squad_leader_lon + lon_offset
    
    def simulate_tactical_movement(self, soldier, time_step):
        """Simulate realistic tactical movement over 90-minute exercise"""
        platoon_data = self.platoons[soldier['platoon']]
        start_loc = self.locations[platoon_data['start_location']]
        objective_loc = self.locations[platoon_data['objective']]
        
        if time_step <= self.movement_samples:
            # Movement Phase (0-60 minutes)
            movement_progress = time_step / self.movement_samples
            
            # Add tactical bounds and realistic movement speed
            # Military units move ~2-4 km/hr in dense terrain
            actual_progress = movement_progress * 0.8  # Don't reach objective during movement phase
            
        else:
            # Engagement Phase (60-90 minutes) 
            # Limited movement, mostly positional adjustments
            actual_progress = 0.8 + (time_step - self.movement_samples) / (self.total_samples - self.movement_samples) * 0.15
        
        # Squad leader determines primary movement
        if soldier['is_squad_leader']:
            # Calculate base position along route
            base_lat = start_loc['lat'] + actual_progress * (objective_loc['lat'] - start_loc['lat'])
            base_lon = start_loc['lon'] + actual_progress * (objective_loc['lon'] - start_loc['lon'])
            
            # Add tactical route deviations (avoiding open areas, using cover)
            route_deviation = 0.00008 * math.sin(time_step * 0.03 + soldier['squad_number'])
            terrain_offset = 0.00005 * math.cos(time_step * 0.02)
            
            final_lat = base_lat + route_deviation + terrain_offset
            final_lon = base_lon + route_deviation * 0.6 + terrain_offset * 0.8
            
        else:
            # Get squad leader position for this time step
            squad_leader = next(s for s in self.soldiers 
                              if s['squad'] == soldier['squad'] and s['is_squad_leader'])
            
            # Calculate squad leader position
            leader_progress = actual_progress
            leader_lat = start_loc['lat'] + leader_progress * (objective_loc['lat'] - start_loc['lat'])
            leader_lon = start_loc['lon'] + leader_progress * (objective_loc['lon'] - start_loc['lon'])
            
            # Add leader's tactical deviations
            route_deviation = 0.00008 * math.sin(time_step * 0.03 + soldier['squad_number'])
            terrain_offset = 0.00005 * math.cos(time_step * 0.02)
            leader_lat += route_deviation + terrain_offset
            leader_lon += route_deviation * 0.6 + terrain_offset * 0.8
            
            # Calculate formation position relative to squad leader
            final_lat, final_lon = self.get_squad_formation_position(
                leader_lat, leader_lon, soldier['position_in_squad'], time_step
            )
        
        return final_lat, final_lon
    
    def simulate_network_performance(self, soldier_lat, soldier_lon, time_step):
        """Simulate 802.11ah mesh network performance with realistic degradation"""
        # Find best MAP connection
        best_rssi = -100
        best_map_id = None
        
        for map_ap in self.mesh_aps:
            rssi = self.calculate_rssi_802_11ah(
                soldier_lat, soldier_lon, 
                map_ap['lat'], map_ap['lon']
            )
            if rssi > best_rssi:
                best_rssi = rssi
                best_map_id = map_ap['id']
        
        # MCS (Modulation and Coding Scheme) based on RSSI for 802.11ah
        if best_rssi > -30:
            mcs = random.randint(8, 10)      # Excellent signal
        elif best_rssi > -45:
            mcs = random.randint(6, 8)       # Good signal
        elif best_rssi > -60:
            mcs = random.randint(4, 6)       # Fair signal
        elif best_rssi > -75:
            mcs = random.randint(2, 4)       # Poor signal
        elif best_rssi > -85:
            mcs = random.randint(0, 2)       # Very poor signal
        else:
            mcs = 0                          # Minimal connectivity
        
        # Network hops in mesh topology
        if best_rssi > -50:
            hops = 1                         # Direct connection to MAP
        elif best_rssi > -70:
            hops = random.randint(1, 2)      # Possible one hop
        else:
            hops = random.randint(2, 4)      # Multiple hops through mesh
        
        # Combat degradation during engagement phase
        if time_step > self.movement_samples:
            # Engagement phase - network stress from movement and interference
            degradation = random.uniform(8, 20)
            best_rssi -= degradation
            mcs = max(0, mcs - random.randint(1, 3))
            hops = min(6, hops + random.randint(0, 2))
        
        return best_rssi, mcs, hops, best_map_id
    
    def simulate_soldier_activity(self, soldier, time_step):
        """Simulate realistic soldier activity patterns throughout exercise"""
        
        if time_step <= self.movement_samples:
            # Movement Phase (0-60 minutes)
            if time_step < 5:  # First 2.5 minutes - preparation
                activity_level = 'Low'
                base_steps = random.randint(5, 15)
                heart_rate = random.randint(70, 85)
            else:  # Active movement
                activity_level = 'Medium'
                base_steps = random.randint(70, 110)
                heart_rate = random.randint(95, 125)
        else:
            # Engagement Phase (60-90 minutes)
            activity_level = 'High'
            base_steps = random.randint(20, 50)  # Less movement, more stationary
            heart_rate = random.randint(130, 170)
        
        # Role-based activity modifications
        if soldier['is_squad_leader']:
            base_steps = int(base_steps * 1.3)  # Leaders move more for coordination
            heart_rate += random.randint(8, 18)
        elif soldier['role'] == 'Medic':
            if time_step > self.movement_samples:
                base_steps = int(base_steps * 1.5)  # Medics busier during engagement
        elif soldier['role'] == 'Automatic Rifleman':
            base_steps = int(base_steps * 0.8)   # Heavy weapon = less movement
        
        # Add individual variation
        personal_factor = 1 + ((hash(soldier['callsign']) % 20) - 10) / 100  # ±10% variation
        base_steps = int(base_steps * personal_factor)
        heart_rate = int(heart_rate * personal_factor)
        
        return activity_level, base_steps, heart_rate
    
    def simulate_equipment_status(self, soldier, time_step):
        """Simulate equipment performance with realistic battery drain"""
        # Initial battery level (soldiers start with different charge levels)
        initial_battery = 85 + ((hash(soldier['callsign']) % 30))  # 85-115% (some over-charged)
        
        # Base drain rate (% per 30-second interval)
        base_drain = 0.8  # ~1.6% per minute
        
        # Role-based power consumption
        if soldier['role'] == 'Squad Leader':
            drain_multiplier = 1.4  # More radio use
        elif soldier['role'] in ['Team Leader Alpha', 'Team Leader Bravo']:
            drain_multiplier = 1.2  # Moderate radio use
        elif soldier['role'] == 'Automatic Rifleman':
            drain_multiplier = 1.1  # Weapon systems
        else:
            drain_multiplier = 1.0
        
        # Activity-based consumption
        if time_step > self.movement_samples:
            drain_multiplier *= 1.3  # Higher consumption during engagement
        
        # Calculate current battery level
        total_drain = time_step * base_drain * drain_multiplier
        current_battery = max(0, initial_battery - total_drain)
        
        # Equipment status
        if current_battery < 15:
            equipment_status = 'Critical'
        elif current_battery < 30:
            equipment_status = 'Warning'  
        elif random.random() < 0.001:  # 0.1% chance of random malfunction
            equipment_status = random.choice(['Warning', 'Critical'])
        else:
            equipment_status = 'Normal'
        
        return round(current_battery, 1), equipment_status
    
    def simulate_combat_casualties(self, soldier, time_step):
        """Simulate combat casualties and medical events during engagement"""
        casualty_state = 'GOOD'
        fall_detection = 0
        
        # Casualties primarily occur during engagement phase
        if time_step > self.movement_samples:
            engagement_progress = (time_step - self.movement_samples) / (self.total_samples - self.movement_samples)
            
            # Peak casualties in middle of engagement
            casualty_risk = 0.002 * math.sin(engagement_progress * math.pi)  # Peak at 50% through engagement
            
            # Role-based casualty risk
            if soldier['role'] == 'Squad Leader':
                casualty_risk *= 1.5  # Leaders at higher risk
            elif soldier['role'] == 'Automatic Rifleman':
                casualty_risk *= 1.3  # Heavy weapons draw fire
            elif soldier['role'] == 'Medic':
                casualty_risk *= 0.7  # Medics somewhat protected
            
            # Check for casualty
            if random.random() < casualty_risk:
                casualty_state = random.choice(['WOUNDED', 'KILLED', 'KILLED', 'KILLED'])  # More KIA than WIA
                fall_detection = 1
        
        # Fall detection without casualty (training accidents)
        elif random.random() < 0.0005:  # 0.05% chance during movement
            fall_detection = 1
        
        # Medical evacuation/resurrection (training exercise)
        if casualty_state == 'KILLED' and random.random() < 0.4:  # 40% get resurrected
            casualty_state = 'RESURRECTED'
        elif casualty_state == 'WOUNDED' and random.random() < 0.6:  # 60% recover
            casualty_state = 'GOOD'
        
        return casualty_state, fall_detection
    
    def determine_posture(self, soldier, time_step, activity_level, casualty_state):
        """Determine soldier posture based on situation"""
        if casualty_state in ['KILLED', 'WOUNDED']:
            return 'Prone'
        
        if time_step <= self.movement_samples:
            # Movement phase
            if activity_level == 'Low':
                return 'Standing'
            else:
                return random.choice(['Standing', 'Kneeling'])
        else:
            # Engagement phase - more tactical postures
            if soldier['role'] == 'Automatic Rifleman':
                return random.choice(['Prone', 'Kneeling'])  # Support weapons
            else:
                # Weighted choice for engagement phase
                rand_val = random.random()
                if rand_val < 0.5:
                    return 'Prone'
                elif rand_val < 0.8:
                    return 'Kneeling'
                else:
                    return 'Standing'
    
    def simulate_environmental_conditions(self, time_step):
        """Simulate Georgia environmental conditions"""
        # Georgia climate - typical training day in spring/fall
        base_temp = 18.0  # Celsius (65°F)
        
        # Daily temperature variation
        time_of_day = (time_step * self.sample_interval_seconds) / 3600  # Hours since start
        daily_variation = 4.0 * math.sin((time_of_day - 3) * math.pi / 12)  # Peak afternoon
        
        # Random weather variation
        weather_noise = random.uniform(-2, 2)
        
        temperature = base_temp + daily_variation + weather_noise
        
        # Humidity inversely related to temperature
        humidity = 75 - (temperature - 18) * 2 + random.uniform(-8, 8)
        humidity = max(40, min(95, humidity))
        
        return round(temperature, 1), round(humidity, 1)
    
    def get_exercise_phase(self, time_step):
        """Determine current exercise phase"""
        if time_step < 10:
            return 'Preparation'
        elif time_step <= self.movement_samples:
            return 'Movement'
        elif time_step <= self.movement_samples + 30:
            return 'Initial Contact'
        elif time_step <= self.total_samples - 10:
            return 'Engagement'
        else:
            return 'Consolidation'
    
    def get_mission_status(self, soldier, time_step):
        """Determine mission status"""
        if time_step < 10:
            return 'Preparing'
        elif time_step <= self.movement_samples * 0.8:
            return 'En Route'
        elif time_step <= self.movement_samples:
            return 'Approaching Objective'
        elif time_step <= self.movement_samples + 20:
            return 'Making Contact'
        elif time_step <= self.total_samples - 10:
            return 'In Combat'
        else:
            return 'Mission Complete'
    
    def generate_complete_exercise_data(self):
        """Generate complete 90-minute exercise with 10,080 position reports"""
        print(f"\n🎖️ Generating Fort Moore Exercise Data...")
        print(f"📊 Expected: {len(self.soldiers)} soldiers × {self.total_samples} reports = {len(self.soldiers) * self.total_samples:,} total records")
        
        data = []
        
        for time_step in range(self.total_samples):
            current_time = self.start_time + timedelta(seconds=time_step * self.sample_interval_seconds)
            
            # Environmental conditions (same for all soldiers at this time)
            temperature, humidity = self.simulate_environmental_conditions(time_step)
            exercise_phase = self.get_exercise_phase(time_step)
            
            for soldier in self.soldiers:
                # Tactical movement simulation
                lat, lon = self.simulate_tactical_movement(soldier, time_step)
                
                # Network performance (802.11ah mesh)
                rssi, mcs, hops, connected_map = self.simulate_network_performance(lat, lon, time_step)
                
                # Soldier activity and biometrics
                activity_level, steps, heart_rate = self.simulate_soldier_activity(soldier, time_step)
                
                # Equipment status and battery
                battery_level, equipment_status = self.simulate_equipment_status(soldier, time_step)
                
                # Combat casualties and medical events
                casualty_state, fall_detection = self.simulate_combat_casualties(soldier, time_step)
                
                # Soldier posture
                posture = self.determine_posture(soldier, time_step, activity_level, casualty_state)
                
                # Mission status
                mission_status = self.get_mission_status(soldier, time_step)
                
                # Create comprehensive data record
                record = {
                    'Timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Unit_ID': soldier['callsign'],
                    'Callsign': soldier['callsign'],
                    'Platoon': soldier['platoon'],
                    'Squad': soldier['squad'],
                    'Squad_Number': soldier['squad_number'],
                    'Position_In_Squad': soldier['position_in_squad'],
                    'Role': soldier['role'],
                    'Latitude': round(lat, 6),
                    'Longitude': round(lon, 6),
                    'Step_Count': steps,
                    'Heart_Rate': heart_rate,
                    'Activity_Level': activity_level,
                    'Posture': posture,
                    'Battery_Level': battery_level,
                    'Equipment_Status': equipment_status,
                    'Fall_Detection': fall_detection,
                    'Casualty_State': casualty_state,
                    'Temperature': temperature,
                    'Humidity': humidity,
                    'RSSI': round(rssi, 1),
                    'MCS': mcs,
                    'Network_Hops': hops,
                    'Connected_MAP': connected_map,
                    'Exercise_Phase': exercise_phase,
                    'Mission_Status': mission_status,
                    'Time_Step': time_step
                }
                
                data.append(record)
            
            # Progress reporting
            if time_step % 30 == 0 or time_step == self.total_samples - 1:
                progress = ((time_step + 1) / self.total_samples) * 100
                records_so_far = len(data)
                print(f"Progress: {progress:5.1f}% | Time: {current_time.strftime('%H:%M:%S')} | Records: {records_so_far:,}")
        
        return pd.DataFrame(data)

def main():
    """Generate and save corrected Fort Moore exercise data"""
    print("🎖️ Fort Moore Training Exercise - Corrected Data Generator")
    print("=" * 70)
    print("Military Structure: 2 Platoons × 4 Squads × 7 Soldiers = 56 Callsigns")
    print("Exercise Duration: 90 minutes (60 min movement + 30 min engagement)")
    print("Position Reports: Every 30 seconds = 180 reports per callsign")
    print("Expected Total: 56 × 180 = 10,080 position reports")
    print("=" * 70)
    
    # Create corrected simulator
    simulator = CorrectedFortMooreSimulator()
    
    # Generate complete exercise data
    exercise_data = simulator.generate_complete_exercise_data()
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"fort_moore_corrected_exercise_{timestamp}.csv"
    exercise_data.to_csv(filename, index=False)
    
    print(f"\n✅ Fort Moore Exercise Data Generated Successfully!")
    print(f"📄 File: {filename}")
    print(f"📊 Total Records: {len(exercise_data):,}")
    print(f"👥 Unique Callsigns: {exercise_data['Callsign'].nunique()}")
    print(f"⏱️ Exercise Duration: {simulator.total_duration_minutes} minutes")
    print(f"📍 Position Reports per Callsign: {len(exercise_data) // exercise_data['Callsign'].nunique()}")
    
    # Verification
    expected_records = 56 * 180
    actual_records = len(exercise_data)
    print(f"\n🔍 Verification:")
    print(f"Expected Records: {expected_records:,}")
    print(f"Actual Records: {actual_records:,}")
    print(f"Match: {'✅ YES' if actual_records == expected_records else '❌ NO'}")
    
    # Exercise statistics
    print(f"\n📋 Exercise Statistics:")
    print(f"Blue Force Soldiers: {len(exercise_data[exercise_data['Platoon'] == 'BLUE_FORCE']['Callsign'].unique())}")
    print(f"OPFOR Soldiers: {len(exercise_data[exercise_data['Platoon'] == 'OPFOR']['Callsign'].unique())}")
    print(f"Total Casualties: {len(exercise_data[exercise_data['Casualty_State'].isin(['KILLED', 'WOUNDED'])])}")
    print(f"Fall Incidents: {exercise_data['Fall_Detection'].sum()}")
    print(f"Equipment Failures: {len(exercise_data[exercise_data['Equipment_Status'] != 'Normal'])}")
    
    # Network performance summary
    print(f"\n🌐 Network Performance (802.11ah @ 900MHz):")
    print(f"Average RSSI: {exercise_data['RSSI'].mean():.1f} dBm")
    print(f"Average MCS: {exercise_data['MCS'].mean():.1f}")
    print(f"Coverage (RSSI > -80): {len(exercise_data[exercise_data['RSSI'] > -80]) / len(exercise_data) * 100:.1f}%")
    print(f"Average Hops: {exercise_data['Network_Hops'].mean():.1f}")
    
    print(f"\n🎯 Ready for AAR Analysis!")
    print(f"This dataset provides comprehensive military exercise data with:")
    print(f"• Proper 56-soldier force structure")
    print(f"• 10,080 position reports as requested") 
    print(f"• Realistic 802.11ah mesh network performance")
    print(f"• Combat casualties and medical events")
    print(f"• Equipment monitoring and battery drain")
    print(f"• Environmental conditions")
    
    return filename

if __name__ == "__main__":
    filename = main()
    print(f"\n💾 Generated file: {filename}")
    print(f"📂 Load this file into your AAR system to test all report capabilities!")
