#!/usr/bin/env python3
"""
Fort Moore Blackhawk Trail Exercise Data Generator

Generates realistic simulated training data following all guidance specifications:
- 4-hour exercise duration with 15-second reporting intervals
- 60 soldiers (30 BLUEFOR, 30 OPFOR) 
- Realistic biometric data with phase-based variations
- Proper casualty rates and distributions
- Geographic coordinates for Fort Moore training area
- Complete time-series data: 57,600 total records

Usage:
    python fort_moore_generator.py [--output filename.csv] [--duration hours] [--interval seconds]
"""

import csv
import datetime
import random
import math
import argparse
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Location:
    """Geographic location"""
    lat: float
    lon: float


@dataclass
class SoldierProfile:
    """Individual soldier characteristics"""
    callsign: str
    is_bluefor: bool
    fitness: str  # 'high', 'average', 'lower'
    role: str     # 'leader', 'medic', 'machinegunner', 'marksman', 'rifleman'
    baseline_temp: float
    baseline_hr: float
    stress_factor: float
    metabolic_factor: float
    weapon: str
    squad: str
    step_count: int = 0
    battery_level: float = 98.0
    current_lat: float = 0.0
    current_lon: float = 0.0
    last_posture: str = 'Standing'


@dataclass
class Casualty:
    """Casualty assignment"""
    callsign: str
    casualty_type: str  # 'KIA' or 'WIA'
    time_minutes: float


class FortMooreDataGenerator:
    """Generates realistic Fort Moore training exercise data"""
    
    def __init__(self, duration_hours: int = 4, reporting_interval_seconds: int = 15):
        self.duration_hours = duration_hours
        self.reporting_interval = reporting_interval_seconds
        self.exercise_start = datetime.datetime(2025, 8, 6, 7, 0, 0)
        
        # Fort Moore training area coordinates
        self.locations = {
            'GENERAL_FIELD': Location(32.387757, -84.797814),      # BLUEFOR start
            'RESIDENTIAL_COMPOUND': Location(32.395052, -84.820543), # OPFOR start  
            'BLACKHAWK_TRAIL': Location(32.383590, -84.813586),     # Primary objective
            'MCKENNA_TOWER': Location(32.366973, -84.813285)        # OPFOR objective
        }
        
        # Force structure
        self.bluefor_callsigns = [f"BLUE{i:02d}" for i in range(1, 31)]
        self.opfor_callsigns = [f"RED{i:02d}" for i in range(1, 31)]
        self.all_callsigns = self.bluefor_callsigns + self.opfor_callsigns
        
        # Squad assignments
        self.squad_assignments = {}
        for i, callsign in enumerate(self.bluefor_callsigns):
            self.squad_assignments[callsign] = 'ALPHA' if i < 15 else 'BRAVO'
        for i, callsign in enumerate(self.opfor_callsigns):
            self.squad_assignments[callsign] = 'CHARLIE' if i < 15 else 'DELTA'
        
        # Calculate exercise parameters
        self.total_minutes = duration_hours * 60
        self.reports_per_minute = 60 // reporting_interval_seconds
        self.total_time_points = self.total_minutes * self.reports_per_minute
        self.expected_records = len(self.all_callsigns) * self.total_time_points
        
        print(f"Exercise Configuration:")
        print(f"  Duration: {duration_hours} hours ({self.total_minutes} minutes)")
        print(f"  Reporting Interval: {reporting_interval_seconds} seconds")
        print(f"  Total Time Points: {self.total_time_points}")
        print(f"  Expected Records: {self.expected_records:,}")
        
        # Initialize soldier profiles and casualties
        self.soldier_profiles = self._create_soldier_profiles()
        self.casualties = self._assign_casualties()
        self.casualty_lookup = {c.callsign: c for c in self.casualties}
        
    def _create_soldier_profiles(self) -> Dict[str, SoldierProfile]:
        """Create individual soldier profiles with realistic characteristics"""
        profiles = {}
        
        for callsign in self.all_callsigns:
            is_bluefor = callsign.startswith('BLUE')
            
            # Assign roles based on callsign ending
            if callsign.endswith('01') or callsign.endswith('16'):
                role = 'leader'
            elif callsign.endswith('02') or callsign.endswith('17'):
                role = 'medic'
            elif callsign.endswith('03') or callsign.endswith('18'):
                role = 'machinegunner'
            elif callsign.endswith('04') or callsign.endswith('19'):
                role = 'marksman'
            else:
                role = 'rifleman'
            
            # Fitness distribution: 60% high, 35% average, 5% lower
            fitness_roll = random.random()
            if fitness_roll < 0.6:
                fitness = 'high'
            elif fitness_roll < 0.95:
                fitness = 'average'
            else:
                fitness = 'lower'
            
            # Baseline biometrics based on fitness
            if fitness == 'high':
                baseline_temp = 97.8 + random.random() * 0.7
                baseline_hr = 50 + random.random() * 15
            elif fitness == 'average':
                baseline_temp = 98.0 + random.random() * 1.0
                baseline_hr = 60 + random.random() * 15
            else:  # lower fitness
                baseline_temp = 98.5 + random.random() * 1.0
                baseline_hr = 70 + random.random() * 15
            
            # Role-based stress factors
            stress_factors = {
                'leader': 0.3,
                'machinegunner': 0.5,
                'marksman': 0.2,
                'medic': 0.4,
                'rifleman': 0.0
            }
            
            # Weapon assignments
            if is_bluefor:
                weapon = 'M240B' if role == 'machinegunner' else 'M4A1'
            else:
                weapon = 'PKM' if role == 'machinegunner' else 'AK-74'
            
            # Starting positions
            start_pos = self.locations['GENERAL_FIELD'] if is_bluefor else self.locations['RESIDENTIAL_COMPOUND']
            
            profile = SoldierProfile(
                callsign=callsign,
                is_bluefor=is_bluefor,
                fitness=fitness,
                role=role,
                baseline_temp=baseline_temp,
                baseline_hr=baseline_hr,
                stress_factor=stress_factors[role],
                metabolic_factor=(random.random() - 0.5) * 0.6,  # ±0.3°F individual variation
                weapon=weapon,
                squad=self.squad_assignments[callsign],
                battery_level=95 + random.random() * 5,
                current_lat=start_pos.lat,
                current_lon=start_pos.lon
            )
            
            profiles[callsign] = profile
        
        return profiles
    
    def _assign_casualties(self) -> List[Casualty]:
        """Assign casualties according to guidance specifications"""
        casualties = []
        
        # OPFOR casualties: 50% KIA (15), 15% WIA (4) = 65% total
        # BLUEFOR casualties: 5% KIA (2), 40% WIA (12) = 45% total
        
        # Combat phase: 90-135 minutes
        combat_start = 90
        combat_duration = 45
        
        # OPFOR casualties
        shuffled_opfor = self.opfor_callsigns.copy()
        random.shuffle(shuffled_opfor)
        
        # 15 OPFOR KIA
        for i in range(15):
            casualties.append(Casualty(
                callsign=shuffled_opfor[i],
                casualty_type='KIA',
                time_minutes=combat_start + random.random() * combat_duration
            ))
        
        # 4 OPFOR WIA
        for i in range(15, 19):
            casualties.append(Casualty(
                callsign=shuffled_opfor[i],
                casualty_type='WIA',
                time_minutes=combat_start + random.random() * combat_duration
            ))
        
        # BLUEFOR casualties
        shuffled_bluefor = self.bluefor_callsigns.copy()
        random.shuffle(shuffled_bluefor)
        
        # 2 BLUEFOR KIA
        for i in range(2):
            casualties.append(Casualty(
                callsign=shuffled_bluefor[i],
                casualty_type='KIA',
                time_minutes=combat_start + random.random() * combat_duration
            ))
        
        # 12 BLUEFOR WIA
        for i in range(2, 14):
            casualties.append(Casualty(
                callsign=shuffled_bluefor[i],
                casualty_type='WIA',
                time_minutes=combat_start + random.random() * combat_duration
            ))
        
        print(f"Casualties Assigned:")
        print(f"  BLUEFOR: {len([c for c in casualties if c.callsign.startswith('BLUE')])} total")
        print(f"    KIA: {len([c for c in casualties if c.callsign.startswith('BLUE') and c.casualty_type == 'KIA'])}")
        print(f"    WIA: {len([c for c in casualties if c.callsign.startswith('BLUE') and c.casualty_type == 'WIA'])}")
        print(f"  OPFOR: {len([c for c in casualties if c.callsign.startswith('RED')])} total")
        print(f"    KIA: {len([c for c in casualties if c.callsign.startswith('RED') and c.casualty_type == 'KIA'])}")
        print(f"    WIA: {len([c for c in casualties if c.callsign.startswith('RED') and c.casualty_type == 'WIA'])}")
        
        return casualties
    
    def _get_exercise_phase(self, minutes: float) -> str:
        """Determine current exercise phase"""
        if minutes < 90:
            return 'preparation'
        elif minutes < 135:
            return 'combat'
        elif minutes < 150:
            return 'consolidation'
        else:
            return 'extended'
    
    def _calculate_biometrics(self, profile: SoldierProfile, minutes: float, 
                            phase: str, casualty_state: str) -> Dict[str, float]:
        """Calculate realistic biometric data based on phase and individual factors"""
        
        # Temperature calculation
        temperature = profile.baseline_temp + profile.metabolic_factor
        
        # Phase-based temperature adjustments (from guidance)
        if phase == 'preparation':
            if minutes < 30:
                temperature += random.uniform(0.0, 0.3)  # Equipment prep
            else:
                temperature += random.uniform(0.5, 2.0)  # Movement to positions
        elif phase == 'combat':
            temperature += random.uniform(1.5, 2.5)  # Combat stress
            if 90 <= minutes <= 95:  # Initial contact spike
                temperature += random.uniform(0.8, 1.5)
        elif phase == 'consolidation':
            temperature += random.uniform(0.2, 1.0)  # Recovery
        else:  # extended
            temperature += random.uniform(0.1, 0.5)
        
        # Role-based stress factor
        temperature += profile.stress_factor
        
        # Casualty impact
        if casualty_state == 'WIA':
            temperature += random.uniform(0.5, 1.5)  # Pain/shock response
        
        # Physiological limits
        temperature = max(95.0, min(106.0, temperature))
        
        # Heart rate calculation
        heart_rate = profile.baseline_hr
        
        # Phase-based heart rate adjustments
        if phase == 'preparation':
            if minutes < 30:
                heart_rate += random.uniform(10, 30)  # Anticipation
            else:
                heart_rate += random.uniform(40, 80)  # Tactical movement
        elif phase == 'combat':
            heart_rate += random.uniform(80, 125)  # Combat stress
            if 90 <= minutes <= 95:  # Initial contact
                heart_rate += random.uniform(40, 60)
        elif phase == 'consolidation':
            heart_rate += random.uniform(15, 40)  # Recovery
        else:  # extended
            heart_rate += random.uniform(10, 25)
        
        # Role-based increases
        role_hr_boost = {
            'leader': 10,
            'machinegunner': 15,
            'medic': 12,
            'marksman': 8,
            'rifleman': 5
        }
        heart_rate += role_hr_boost[profile.role]
        
        # Casualty impact
        if casualty_state == 'WIA':
            heart_rate += random.uniform(20, 40)
        
        # Physiological limits
        max_hr = 220 - 25  # Assume average age 25
        heart_rate = max(30, min(max_hr, heart_rate))
        
        return {
            'temperature': round(temperature, 1),
            'heart_rate': round(heart_rate)
        }
    
    def _calculate_posture(self, profile: SoldierProfile, phase: str, casualty_state: str) -> str:
        """Calculate soldier posture based on phase and situation"""
        
        if casualty_state != 'GOOD':
            return 'Down'
        
        # Phase-based posture probabilities (from guidance)
        if phase == 'preparation':
            rand = random.random()
            if rand < 0.7:
                posture = 'Standing'
            elif rand < 0.9:
                posture = 'Moving'
            else:
                posture = 'Prone'
        elif phase == 'combat':
            rand = random.random()
            if rand < 0.6:
                posture = 'Prone'      # 60% prone during combat
            elif rand < 0.85:
                posture = 'Standing'   # 25% standing
            else:
                posture = 'Moving'     # 15% moving
        else:  # consolidation or extended
            rand = random.random()
            if rand < 0.8:
                posture = 'Standing'
            elif rand < 0.95:
                posture = 'Prone'
            else:
                posture = 'Moving'
        
        profile.last_posture = posture
        return posture
    
    def _update_step_count(self, profile: SoldierProfile, posture: str, phase: str) -> int:
        """Update cumulative step count based on posture and phase"""
        
        step_increment = 0
        
        if posture == 'Moving':
            if phase == 'combat':
                step_increment = random.uniform(2, 6)  # Limited movement in combat
            else:
                step_increment = random.uniform(4, 12)  # More movement in other phases
        elif posture == 'Standing':
            step_increment = random.uniform(0, 1)  # Minimal movement while standing
        # No steps added for Prone or Down
        
        profile.step_count += step_increment
        return round(profile.step_count)
    
    def _calculate_position(self, profile: SoldierProfile, minutes: float, phase: str) -> Tuple[float, float]:
        """Calculate soldier position based on tactical movement"""
        
        target_lat = profile.current_lat
        target_lon = profile.current_lon
        
        # Movement logic based on phase
        if phase == 'preparation' and minutes > 30:
            # Move toward objectives during preparation phase
            if profile.is_bluefor:
                target = self.locations['BLACKHAWK_TRAIL']
                start = self.locations['GENERAL_FIELD']
            else:
                target = self.locations['MCKENNA_TOWER']
                start = self.locations['RESIDENTIAL_COMPOUND']
            
            # Calculate movement progress (over 60 minutes of movement)
            progress = min(1.0, (minutes - 30) / 60)
            target_lat = start.lat + (target.lat - start.lat) * progress
            target_lon = start.lon + (target.lon - start.lon) * progress
            
            # Add tactical dispersion
            target_lat += random.uniform(-0.003, 0.003)
            target_lon += random.uniform(-0.003, 0.003)
            
        elif phase == 'combat':
            # Tactical movement around objectives during combat
            center = self.locations['BLACKHAWK_TRAIL'] if profile.is_bluefor else self.locations['MCKENNA_TOWER']
            target_lat = center.lat + random.uniform(-0.004, 0.004)
            target_lon = center.lon + random.uniform(-0.004, 0.004)
            
        else:
            # Minimal movement during other phases
            target_lat = profile.current_lat + random.uniform(-0.0005, 0.0005)
            target_lon = profile.current_lon + random.uniform(-0.0005, 0.0005)
        
        # Smooth position changes (no teleporting)
        max_movement = 0.0002  # Max change per 15-second interval
        lat_diff = target_lat - profile.current_lat
        lon_diff = target_lon - profile.current_lon
        
        # Apply movement limits
        lat_change = max(-max_movement, min(max_movement, lat_diff))
        lon_change = max(-max_movement, min(max_movement, lon_diff))
        
        profile.current_lat += lat_change
        profile.current_lon += lon_change
        
        return round(profile.current_lat, 6), round(profile.current_lon, 6)
    
    def _calculate_technical_data(self) -> Dict[str, any]:
        """Calculate technical network data"""
        
        # RSSI varies by position and terrain (-40 to -80 dBm)
        base_rssi = -50
        terrain_factor = random.uniform(0, 30)
        rssi = round(base_rssi - terrain_factor)
        
        # MCS (0-15) adaptive based on signal quality
        mcs = max(0, min(15, round(15 * (-rssi + 40) / 40)))
        
        # NextHop routing
        nexthops = ['RELAY-01', 'RELAY-02', 'RELAY-03', 'BASE-STATION', 'GATEWAY']
        nexthop = random.choice(nexthops)
        
        return {
            'rssi': rssi,
            'mcs': mcs,
            'nexthop': nexthop
        }
    
    def _calculate_engagement(self, profile: SoldierProfile, phase: str) -> Dict[str, Optional[str]]:
        """Calculate engagement data (shooter, munition, hit zone)"""
        
        shooter = None
        munition = None
        hitzone = None
        
        # Engagements only during combat phase with very low probability
        if phase == 'combat' and random.random() < 0.0005:
            # Select random enemy shooter
            enemy_force = self.opfor_callsigns if profile.is_bluefor else self.bluefor_callsigns
            shooter = random.choice(enemy_force)
            
            # Munition type based on typical enemy weapons
            munition = '7.62mm' if profile.is_bluefor else '5.56mm'
            
            # Hit zone distribution (from guidance)
            hit_roll = random.random()
            if hit_roll < 0.6:
                hitzone = 'Torso'      # 60% center mass
            elif hit_roll < 0.9:
                hitzone = 'Extremity'  # 30% arms/legs
            else:
                hitzone = 'Head'       # 10% head shots
        
        return {
            'shooter': shooter or '',
            'munition': munition or '',
            'hitzone': hitzone or ''
        }
    
    def generate_csv(self, output_filename: str) -> None:
        """Generate complete time-series CSV dataset"""
        
        print(f"\nGenerating complete time-series dataset...")
        print(f"Output file: {output_filename}")
        
        # CSV headers (including heartrate per guidance)
        headers = [
            'callsign', 'squad', 'ip', 'playerid', 'casualtystate', 'processedtimegmt',
            'latitude', 'longitude', 'battery', 'posture', 'shootercallsign', 'weapon',
            'munition', 'hitzone', 'temp', 'rssi', 'mcs', 'nexthop', 'stepcount',
            'falldetected', 'heartrate'
        ]
        
        records_written = 0
        
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            # Generate data for each time point
            for time_point in range(self.total_time_points):
                # Calculate current time
                seconds_elapsed = time_point * self.reporting_interval
                current_time = self.exercise_start + datetime.timedelta(seconds=seconds_elapsed)
                minutes_elapsed = seconds_elapsed / 60
                
                # Format timestamp
                time_string = current_time.strftime("%m/%d/%Y %H:%M:%S")
                
                # Determine current phase
                phase = self._get_exercise_phase(minutes_elapsed)
                
                # Process each soldier for this time point
                for callsign in self.all_callsigns:
                    profile = self.soldier_profiles[callsign]
                    
                    # Check casualty status
                    casualty_state = 'GOOD'
                    if callsign in self.casualty_lookup:
                        casualty = self.casualty_lookup[callsign]
                        if minutes_elapsed >= casualty.time_minutes:
                            casualty_state = casualty.casualty_type
                            # KIA soldiers stop reporting
                            if casualty.casualty_type == 'KIA':
                                continue
                    
                    # Generate all data for this soldier at this time
                    biometrics = self._calculate_biometrics(profile, minutes_elapsed, phase, casualty_state)
                    posture = self._calculate_posture(profile, phase, casualty_state)
                    step_count = self._update_step_count(profile, posture, phase)
                    lat, lon = self._calculate_position(profile, minutes_elapsed, phase)
                    technical = self._calculate_technical_data()
                    engagement = self._calculate_engagement(profile, phase)
                    
                    # Calculate other fields
                    battery = max(0, round(profile.battery_level - (minutes_elapsed * 0.006)))  # 1.5% per hour
                    fall_detected = 'Yes' if (phase == 'preparation' and posture == 'Moving' and random.random() < 0.0001) else 'No'
                    
                    # Create record
                    record = [
                        callsign,
                        profile.squad,
                        f"10.1.{'1' if profile.is_bluefor else '2'}.{callsign[-2:]}",
                        1001 + int(callsign[-2:]) - 1 if profile.is_bluefor else 1031 + int(callsign[-2:]) - 1,
                        casualty_state,
                        time_string,
                        lat,
                        lon,
                        battery,
                        posture,
                        engagement['shooter'],
                        profile.weapon,
                        engagement['munition'],
                        engagement['hitzone'],
                        biometrics['temperature'],
                        technical['rssi'],
                        technical['mcs'],
                        technical['nexthop'],
                        step_count,
                        fall_detected,
                        biometrics['heart_rate']
                    ]
                    
                    writer.writerow(record)
                    records_written += 1
                
                # Progress reporting
                if time_point % (self.total_time_points // 20) == 0:  # 20 progress updates
                    percent_complete = (time_point / self.total_time_points) * 100
                    print(f"  Progress: {percent_complete:.1f}% - {records_written:,} records written")
        
        print(f"\nGeneration complete!")
        print(f"  Total records written: {records_written:,}")
        print(f"  File size: {self._get_file_size(output_filename)}")
        print(f"  Time span: {self.exercise_start.strftime('%Y-%m-%d %H:%M:%S')} to " +
              f"{(self.exercise_start + datetime.timedelta(hours=self.duration_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _get_file_size(self, filename: str) -> str:
        """Get human-readable file size"""
        try:
            import os
            size_bytes = os.path.getsize(filename)
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/(1024**2):.1f} MB"
            else:
                return f"{size_bytes/(1024**3):.1f} GB"
        except:
            return "unknown"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Fort Moore training exercise CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fort_moore_generator.py
  python fort_moore_generator.py --output my_data.csv
  python fort_moore_generator.py --duration 2 --interval 30
  python fort_moore_generator.py --output data.csv --duration 4 --interval 15
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='fort_moore_training_data.csv',
        help='Output CSV filename (default: fort_moore_training_data.csv)'
    )
    
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=4,
        help='Exercise duration in hours (default: 4)'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=15,
        help='Reporting interval in seconds (default: 15)'
    )
    
    parser.add_argument(
        '--seed', '-s',
        type=int,
        help='Random seed for reproducible results'
    )
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)
        print(f"Random seed set to: {args.seed}")
    
    # Validate arguments
    if args.duration <= 0:
        print("Error: Duration must be positive", file=sys.stderr)
        sys.exit(1)
    
    if args.interval <= 0 or args.interval > 3600:
        print("Error: Interval must be between 1 and 3600 seconds", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create generator and generate data
        generator = FortMooreDataGenerator(
            duration_hours=args.duration,
            reporting_interval_seconds=args.interval
        )
        
        generator.generate_csv(args.output)
        
        print(f"\n✅ Successfully generated Fort Moore training data:")
        print(f"   File: {args.output}")
        print(f"   Duration: {args.duration} hours")
        print(f"   Interval: {args.interval} seconds")
        print(f"   Records: {generator.expected_records:,}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error generating data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
