#!/usr/bin/env python3
"""
CDSI Regulatory Module Loader

Dynamic loading system for regulatory compliance modules based on jurisdiction,
industry, and functional requirements. Implements modular architecture for
scalable compliance coverage.

Features:
- Dynamic module loading based on tier level
- Jurisdiction-specific pattern loading
- Industry vertical support
- Configurable module combinations

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import json
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Type
from dataclasses import dataclass, field
from enum import Enum
import yaml
from datetime import datetime

from ..core.heuristics_engine import TierLevel, PatternDefinition

# Configure logging
logger = logging.getLogger(__name__)

class ModuleType(Enum):
    """Types of regulatory modules"""
    GEOGRAPHIC = "geographic"
    INDUSTRY = "industry" 
    FUNCTIONAL = "functional"
    SCALE = "scale"

class ModuleStatus(Enum):
    """Module loading status"""
    LOADED = "loaded"
    FAILED = "failed"
    DISABLED = "disabled"
    PENDING = "pending"

@dataclass
class ModuleDefinition:
    """Regulatory module definition"""
    id: str
    name: str
    module_type: ModuleType
    jurisdiction: str
    tier_level: TierLevel
    dependencies: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    active: bool = True
    patterns_file: Optional[str] = None
    config_file: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass 
class LoadedModule:
    """Loaded regulatory module with patterns"""
    definition: ModuleDefinition
    patterns: Dict[str, PatternDefinition]
    status: ModuleStatus
    load_time: str
    error_message: Optional[str] = None

class RegulatoryModuleLoader:
    """
    Dynamic loader for regulatory compliance modules
    
    Manages loading, validation, and configuration of regulatory modules
    based on customer tier level and selected jurisdictions/industries.
    """
    
    def __init__(self, modules_dir: str = "src/modules/definitions"):
        self.modules_dir = Path(modules_dir)
        self.loaded_modules: Dict[str, LoadedModule] = {}
        self.available_modules: Dict[str, ModuleDefinition] = {}
        self.tier_level = TierLevel.AWARE
        
        # Initialize module directory
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Load available module definitions
        self._discover_modules()
        
        logger.info(f"Regulatory Module Loader initialized with {len(self.available_modules)} available modules")
    
    def _discover_modules(self):
        """Discover available regulatory modules"""
        try:
            # Look for module definition files
            for module_file in self.modules_dir.glob("**/*.yaml"):
                try:
                    with open(module_file, 'r') as f:
                        module_data = yaml.safe_load(f)
                    
                    # Convert to ModuleDefinition
                    module_def = ModuleDefinition(
                        id=module_data['id'],
                        name=module_data['name'],
                        module_type=ModuleType(module_data['type']),
                        jurisdiction=module_data['jurisdiction'],
                        tier_level=TierLevel(module_data.get('tier_level', 'aware')),
                        dependencies=module_data.get('dependencies', []),
                        version=module_data.get('version', '1.0.0'),
                        active=module_data.get('active', True),
                        patterns_file=module_data.get('patterns_file'),
                        config_file=module_data.get('config_file')
                    )
                    
                    self.available_modules[module_def.id] = module_def
                    
                except Exception as e:
                    logger.error(f"Failed to load module definition from {module_file}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to discover modules: {e}")
        
        # Create default modules if none found
        if not self.available_modules:
            self._create_default_modules()
    
    def _create_default_modules(self):
        """Create default regulatory modules"""
        default_modules = {
            # US Federal Module
            'us_federal': ModuleDefinition(
                id='us_federal',
                name='US Federal Compliance',
                module_type=ModuleType.GEOGRAPHIC,
                jurisdiction='US_FEDERAL',
                tier_level=TierLevel.AWARE,
                patterns_file='us_federal_patterns.yaml'
            ),
            
            # GDPR Module
            'eu_gdpr': ModuleDefinition(
                id='eu_gdpr', 
                name='EU GDPR Compliance',
                module_type=ModuleType.GEOGRAPHIC,
                jurisdiction='EU',
                tier_level=TierLevel.AWARE,
                patterns_file='eu_gdpr_patterns.yaml'
            ),
            
            # California CCPA Module
            'us_ca_ccpa': ModuleDefinition(
                id='us_ca_ccpa',
                name='California CCPA/CPRA',
                module_type=ModuleType.GEOGRAPHIC, 
                jurisdiction='US_CA',
                tier_level=TierLevel.AWARE,
                dependencies=['us_federal'],
                patterns_file='ca_ccpa_patterns.yaml'
            ),
            
            # Texas Privacy Module
            'us_tx_privacy': ModuleDefinition(
                id='us_tx_privacy',
                name='Texas Privacy & AI Laws',
                module_type=ModuleType.GEOGRAPHIC,
                jurisdiction='US_TX',
                tier_level=TierLevel.BUILDER,
                dependencies=['us_federal'],
                patterns_file='tx_privacy_patterns.yaml'
            ),
            
            # Healthcare Industry Module
            'industry_healthcare': ModuleDefinition(
                id='industry_healthcare',
                name='Healthcare Compliance (HIPAA)',
                module_type=ModuleType.INDUSTRY,
                jurisdiction='GLOBAL',
                tier_level=TierLevel.BUILDER,
                patterns_file='healthcare_patterns.yaml'
            ),
            
            # Financial Industry Module
            'industry_financial': ModuleDefinition(
                id='industry_financial',
                name='Financial Services Compliance',
                module_type=ModuleType.INDUSTRY,
                jurisdiction='GLOBAL',
                tier_level=TierLevel.BUILDER,
                patterns_file='financial_patterns.yaml'
            ),
            
            # Privacy Rights Functional Module
            'func_privacy_rights': ModuleDefinition(
                id='func_privacy_rights',
                name='Privacy Rights Management',
                module_type=ModuleType.FUNCTIONAL,
                jurisdiction='GLOBAL',
                tier_level=TierLevel.ACCELERATOR,
                patterns_file='privacy_rights_patterns.yaml'
            ),
            
            # AI Governance Functional Module
            'func_ai_governance': ModuleDefinition(
                id='func_ai_governance',
                name='AI Governance & Ethics',
                module_type=ModuleType.FUNCTIONAL,
                jurisdiction='GLOBAL',
                tier_level=TierLevel.TRANSFORMER,
                patterns_file='ai_governance_patterns.yaml'
            )
        }
        
        self.available_modules.update(default_modules)
        
        # Save default module definitions
        for module_id, module_def in default_modules.items():
            self._save_module_definition(module_def)
        
        # Create default pattern files
        self._create_default_patterns()
    
    def _save_module_definition(self, module_def: ModuleDefinition):
        """Save module definition to file"""
        try:
            module_file = self.modules_dir / f"{module_def.id}.yaml"
            module_data = {
                'id': module_def.id,
                'name': module_def.name,
                'type': module_def.module_type.value,
                'jurisdiction': module_def.jurisdiction,
                'tier_level': module_def.tier_level.value,
                'dependencies': module_def.dependencies,
                'version': module_def.version,
                'active': module_def.active,
                'patterns_file': module_def.patterns_file,
                'config_file': module_def.config_file,
                'created_at': module_def.created_at
            }
            
            with open(module_file, 'w') as f:
                yaml.dump(module_data, f, default_flow_style=False)
                
        except Exception as e:
            logger.error(f"Failed to save module definition {module_def.id}: {e}")
    
    def _create_default_patterns(self):
        """Create default pattern files for modules"""
        patterns_dir = self.modules_dir / "patterns"
        patterns_dir.mkdir(exist_ok=True)
        
        # US Federal patterns
        us_federal_patterns = {
            'patterns': [
                {
                    'id': 'coppa_001',
                    'text': r'\bCOPPA\b|\bChildren\'s Online Privacy Protection Act\b',
                    'category': 'privacy_data',
                    'risk_weight': 2.0,
                    'jurisdiction': 'US_FEDERAL'
                },
                {
                    'id': 'hipaa_001', 
                    'text': r'\bHIPAA\b|\bHealth Insurance Portability\b',
                    'category': 'privacy_data',
                    'risk_weight': 2.5,
                    'jurisdiction': 'US_FEDERAL'
                },
                {
                    'id': 'ftc_001',
                    'text': r'\bFTC\b|\bFederal Trade Commission\b',
                    'category': 'enforcement_risk',
                    'risk_weight': 2.2,
                    'jurisdiction': 'US_FEDERAL'
                }
            ]
        }
        
        # EU GDPR patterns
        eu_gdpr_patterns = {
            'patterns': [
                {
                    'id': 'gdpr_001',
                    'text': r'\bGDPR\b|\bGeneral Data Protection Regulation\b',
                    'category': 'privacy_data',
                    'risk_weight': 3.0,
                    'jurisdiction': 'EU'
                },
                {
                    'id': 'dpa_001',
                    'text': r'\bData Protection Authority\b|\bDPA\b',
                    'category': 'enforcement_risk',
                    'risk_weight': 2.5,
                    'jurisdiction': 'EU'
                },
                {
                    'id': 'dpo_001',
                    'text': r'\bData Protection Officer\b|\bDPO\b',
                    'category': 'compliance_process',
                    'risk_weight': 1.8,
                    'jurisdiction': 'EU'
                }
            ]
        }
        
        # California CCPA patterns
        ca_ccpa_patterns = {
            'patterns': [
                {
                    'id': 'ccpa_001',
                    'text': r'\bCCPA\b|\bCalifornia Consumer Privacy Act\b',
                    'category': 'privacy_data', 
                    'risk_weight': 2.8,
                    'jurisdiction': 'US_CA'
                },
                {
                    'id': 'cpra_001',
                    'text': r'\bCPRA\b|\bCalifornia Privacy Rights Act\b',
                    'category': 'privacy_data',
                    'risk_weight': 2.9,
                    'jurisdiction': 'US_CA'
                },
                {
                    'id': 'ca_ag_001',
                    'text': r'\bCalifornia Attorney General\b',
                    'category': 'enforcement_risk',
                    'risk_weight': 2.3,
                    'jurisdiction': 'US_CA'
                }
            ]
        }
        
        # Texas Privacy patterns
        tx_privacy_patterns = {
            'patterns': [
                {
                    'id': 'tx_hb4_001',
                    'text': r'\bTexas Data Privacy and Security Act\b|\bHB\s*4\b',
                    'category': 'privacy_data',
                    'risk_weight': 2.5,
                    'jurisdiction': 'US_TX'
                },
                {
                    'id': 'tx_ai_001', 
                    'text': r'\bTexas AI Advisory Council\b|\bSB\s*2286\b',
                    'category': 'ai_tech',
                    'risk_weight': 2.2,
                    'jurisdiction': 'US_TX'
                },
                {
                    'id': 'tx_ag_001',
                    'text': r'\bTexas Attorney General\b',
                    'category': 'enforcement_risk',
                    'risk_weight': 2.1,
                    'jurisdiction': 'US_TX'
                }
            ]
        }
        
        # Healthcare patterns
        healthcare_patterns = {
            'patterns': [
                {
                    'id': 'phi_001',
                    'text': r'\bPHI\b|\bprotected health information\b',
                    'category': 'privacy_data',
                    'risk_weight': 3.0,
                    'jurisdiction': 'GLOBAL'
                },
                {
                    'id': 'hitech_001',
                    'text': r'\bHITECH\b|\bHealth Information Technology\b',
                    'category': 'privacy_data',
                    'risk_weight': 2.3,
                    'jurisdiction': 'GLOBAL'
                },
                {
                    'id': 'medical_device_001',
                    'text': r'\bmedical device\b|\bFDA approval\b',
                    'category': 'compliance_process',
                    'risk_weight': 2.0,
                    'jurisdiction': 'GLOBAL'
                }
            ]
        }
        
        # Save pattern files
        pattern_files = {
            'us_federal_patterns.yaml': us_federal_patterns,
            'eu_gdpr_patterns.yaml': eu_gdpr_patterns,
            'ca_ccpa_patterns.yaml': ca_ccpa_patterns,
            'tx_privacy_patterns.yaml': tx_privacy_patterns,
            'healthcare_patterns.yaml': healthcare_patterns
        }
        
        for filename, patterns in pattern_files.items():
            try:
                with open(patterns_dir / filename, 'w') as f:
                    yaml.dump(patterns, f, default_flow_style=False)
            except Exception as e:
                logger.error(f"Failed to create pattern file {filename}: {e}")
    
    def set_tier_level(self, tier: TierLevel):
        """Set the current tier level for module loading"""
        self.tier_level = tier
        logger.info(f"Module loader tier level set to: {tier.value}")
    
    def get_available_modules(self, tier: Optional[TierLevel] = None) -> List[ModuleDefinition]:
        """Get modules available for specified tier level"""
        if tier is None:
            tier = self.tier_level
        
        tier_hierarchy = [
            TierLevel.AWARE,
            TierLevel.BUILDER, 
            TierLevel.ACCELERATOR,
            TierLevel.TRANSFORMER,
            TierLevel.CHAMPION
        ]
        
        current_tier_index = tier_hierarchy.index(tier)
        available = []
        
        for module in self.available_modules.values():
            if not module.active:
                continue
                
            module_tier_index = tier_hierarchy.index(module.tier_level)
            if module_tier_index <= current_tier_index:
                available.append(module)
        
        return available
    
    def load_module(self, module_id: str) -> Optional[LoadedModule]:
        """Load a specific regulatory module"""
        if module_id not in self.available_modules:
            logger.error(f"Module {module_id} not found")
            return None
        
        if module_id in self.loaded_modules:
            return self.loaded_modules[module_id]
        
        module_def = self.available_modules[module_id]
        
        try:
            # Check tier level access
            available_modules = self.get_available_modules()
            if module_def not in available_modules:
                error_msg = f"Module {module_id} not available at tier {self.tier_level.value}"
                logger.warning(error_msg)
                return LoadedModule(
                    definition=module_def,
                    patterns={},
                    status=ModuleStatus.DISABLED,
                    load_time=datetime.now().isoformat(),
                    error_message=error_msg
                )
            
            # Load dependencies first
            for dep_id in module_def.dependencies:
                if dep_id not in self.loaded_modules:
                    dep_module = self.load_module(dep_id)
                    if not dep_module or dep_module.status != ModuleStatus.LOADED:
                        error_msg = f"Failed to load dependency {dep_id} for module {module_id}"
                        logger.error(error_msg)
                        return LoadedModule(
                            definition=module_def,
                            patterns={},
                            status=ModuleStatus.FAILED,
                            load_time=datetime.now().isoformat(),
                            error_message=error_msg
                        )
            
            # Load patterns
            patterns = self._load_module_patterns(module_def)
            
            # Create loaded module
            loaded_module = LoadedModule(
                definition=module_def,
                patterns=patterns,
                status=ModuleStatus.LOADED,
                load_time=datetime.now().isoformat()
            )
            
            self.loaded_modules[module_id] = loaded_module
            logger.info(f"Successfully loaded module {module_id} with {len(patterns)} patterns")
            
            return loaded_module
        
        except Exception as e:
            error_msg = f"Failed to load module {module_id}: {str(e)}"
            logger.error(error_msg)
            
            failed_module = LoadedModule(
                definition=module_def,
                patterns={},
                status=ModuleStatus.FAILED,
                load_time=datetime.now().isoformat(),
                error_message=error_msg
            )
            
            self.loaded_modules[module_id] = failed_module
            return failed_module
    
    def _load_module_patterns(self, module_def: ModuleDefinition) -> Dict[str, PatternDefinition]:
        """Load patterns for a specific module"""
        patterns = {}
        
        if not module_def.patterns_file:
            return patterns
        
        patterns_file = self.modules_dir / "patterns" / module_def.patterns_file
        
        try:
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = yaml.safe_load(f)
                
                for pattern_data in patterns_data.get('patterns', []):
                    pattern = PatternDefinition(
                        id=pattern_data['id'],
                        text=pattern_data['text'],
                        category=pattern_data['category'],
                        risk_weight=pattern_data['risk_weight'],
                        tier_level=module_def.tier_level,
                        jurisdiction=pattern_data.get('jurisdiction', module_def.jurisdiction)
                    )
                    patterns[pattern.id] = pattern
            
        except Exception as e:
            logger.error(f"Failed to load patterns from {patterns_file}: {e}")
        
        return patterns
    
    def load_modules(self, module_ids: List[str]) -> Dict[str, LoadedModule]:
        """Load multiple modules"""
        loaded = {}
        
        for module_id in module_ids:
            module = self.load_module(module_id)
            if module:
                loaded[module_id] = module
        
        return loaded
    
    def get_all_patterns(self) -> Dict[str, PatternDefinition]:
        """Get all patterns from loaded modules"""
        all_patterns = {}
        
        for loaded_module in self.loaded_modules.values():
            if loaded_module.status == ModuleStatus.LOADED:
                all_patterns.update(loaded_module.patterns)
        
        return all_patterns
    
    def get_module_stats(self) -> Dict[str, Any]:
        """Get module loading statistics"""
        total_available = len(self.available_modules)
        total_loaded = len([m for m in self.loaded_modules.values() if m.status == ModuleStatus.LOADED])
        total_failed = len([m for m in self.loaded_modules.values() if m.status == ModuleStatus.FAILED])
        total_disabled = len([m for m in self.loaded_modules.values() if m.status == ModuleStatus.DISABLED])
        
        # Category breakdown
        category_stats = {}
        for module_def in self.available_modules.values():
            module_type = module_def.module_type.value
            if module_type not in category_stats:
                category_stats[module_type] = {'available': 0, 'loaded': 0}
            category_stats[module_type]['available'] += 1
            
            if module_def.id in self.loaded_modules:
                loaded_module = self.loaded_modules[module_def.id]
                if loaded_module.status == ModuleStatus.LOADED:
                    category_stats[module_type]['loaded'] += 1
        
        # Pattern count
        total_patterns = sum(len(m.patterns) for m in self.loaded_modules.values() 
                           if m.status == ModuleStatus.LOADED)
        
        return {
            'tier_level': self.tier_level.value,
            'modules': {
                'available': total_available,
                'loaded': total_loaded,
                'failed': total_failed,
                'disabled': total_disabled
            },
            'categories': category_stats,
            'total_patterns': total_patterns,
            'available_for_tier': len(self.get_available_modules())
        }
    
    def unload_module(self, module_id: str) -> bool:
        """Unload a specific module"""
        if module_id in self.loaded_modules:
            del self.loaded_modules[module_id]
            logger.info(f"Unloaded module {module_id}")
            return True
        return False
    
    def reload_module(self, module_id: str) -> Optional[LoadedModule]:
        """Reload a specific module"""
        self.unload_module(module_id)
        return self.load_module(module_id)
    
    def get_loaded_modules(self) -> Dict[str, LoadedModule]:
        """Get all currently loaded modules"""
        return self.loaded_modules.copy()

def main():
    """Test the regulatory module loader"""
    print("📦 CDSI Regulatory Module Loader Test")
    print("=" * 50)
    
    # Initialize loader
    loader = RegulatoryModuleLoader()
    
    # Set tier level
    loader.set_tier_level(TierLevel.BUILDER)
    
    # Show available modules
    available = loader.get_available_modules()
    print(f"\n📋 Available Modules for {loader.tier_level.value} tier:")
    for module in available:
        print(f"  - {module.id}: {module.name} ({module.module_type.value})")
    
    # Load some modules
    print(f"\n🔄 Loading modules...")
    test_modules = ['us_federal', 'eu_gdpr', 'us_ca_ccpa', 'industry_healthcare']
    
    for module_id in test_modules:
        if module_id in loader.available_modules:
            loaded = loader.load_module(module_id)
            if loaded:
                status_icon = "✅" if loaded.status == ModuleStatus.LOADED else "❌"
                print(f"  {status_icon} {module_id}: {loaded.status.value}")
                if loaded.error_message:
                    print(f"     Error: {loaded.error_message}")
    
    # Show statistics
    print(f"\n📊 Module Statistics:")
    stats = loader.get_module_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    # Show all loaded patterns
    all_patterns = loader.get_all_patterns()
    print(f"\n🎯 Total Patterns Loaded: {len(all_patterns)}")
    
    # Show pattern breakdown by category
    category_counts = {}
    for pattern in all_patterns.values():
        category = pattern.category
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"\n📂 Pattern Categories:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} patterns")

if __name__ == "__main__":
    main()