"""FAM Scrapers Module - Global Grocery Retailer Scrapers"""
from .base_scraper import BaseScraper, APIBasedScraper

# US Scrapers
from .walmart_scraper import WalmartScraper, create_walmart_scraper
from .target_scraper import TargetScraper, create_target_scraper
from .north_america_scraper import (
    KrogerScraper, CostcoScraper, SafewayScraper, PublixScraper, LoblawsScraper,
    create_kroger_scraper, create_costco_scraper, create_safeway_scraper,
    create_publix_scraper, create_loblaws_scraper
)

# South America Scrapers
from .south_america_scraper import (
    CencosudScraper, GrupoExitoScraper, PaoDeAcucarScraper, CotoScraper,
    create_cencosud_scraper, create_grupo_exito_scraper, 
    create_pao_de_acucar_scraper, create_coto_scraper
)

# UK Scrapers
from .generic_scraper import TescoScraper, create_tesco_scraper
from .uk_scraper import (
    SainsburysScraper, ASDASScraper, MorrisonsScraper, WaitroseScraper, IcelandScraper,
    create_sainsburys_scraper, create_asda_scraper, create_morrisons_scraper,
    create_waitrose_scraper, create_iceland_scraper
)

# Europe Scrapers
from .generic_scraper import CarrefourScraper, create_carrefour_scraper

# Australia/NZ Scrapers
from .generic_scraper import WoolworthsScraper, create_woolworths_scraper
from .australia_nz_scraper import (
    ColesScraper, IGAScraper, CountdownScraper, PaknSaveScraper, NewWorldScraper,
    create_coles_scraper, create_iga_scraper, create_countdown_scraper,
    create_paknsave_scraper, create_newworld_scraper
)

# Asia Scrapers
from .asia_scraper import (
    FairPriceScraper, BigBazaarScraper, DMartScraper, AeonScraper, 
    EMartScraper, LotteMartScraper,
    create_fairprice_scraper, create_bigbazaar_scraper, create_dmart_scraper,
    create_aeon_scraper, create_emart_scraper, create_lottemart_scraper
)

# China Scrapers
from .china_scraper import (
    FreshippoScraper, RTMartScraper, YonghuiScraper, WumartScraper,
    create_freshippo_scraper, create_rtmart_scraper, 
    create_yonghui_scraper, create_wumart_scraper
)

# Middle East & Turkey Scrapers
from .middle_east_scraper import (
    LuluHypermarketScraper, SpinneysScraper, ChoithramsScraper,
    MigrosTurkeyScraper, BIMScraper, A101Scraper,
    create_lulu_scraper, create_spinneys_scraper, create_choithrams_scraper,
    create_migros_turkey_scraper, create_bim_scraper, create_a101_scraper
)

# Russia Scrapers
from .russia_scraper import (
    MagnitScraper, X5RetailScraper, LentaScraper, PerekrestokScraper,
    create_magnit_scraper, create_pyaterochka_scraper, 
    create_lenta_scraper, create_perekrestok_scraper
)

# Africa Scrapers
from .africa_scraper import (
    ShopriteScraper, PicknPayScraper, CheckersScraper, WoolworthsSAScraper,
    create_shoprite_scraper, create_picknpay_scraper, 
    create_checkers_scraper, create_woolworths_sa_scraper
)

# Pipeline
from .pipeline import DataPipeline, ScraperRegistry, run_pipeline

__all__ = [
    # Base
    'BaseScraper', 'APIBasedScraper',
    # Pipeline
    'DataPipeline', 'ScraperRegistry', 'run_pipeline',
    # US
    'WalmartScraper', 'TargetScraper', 'KrogerScraper', 'CostcoScraper', 
    'SafewayScraper', 'PublixScraper', 'LoblawsScraper',
    # South America
    'CencosudScraper', 'GrupoExitoScraper', 'PaoDeAcucarScraper', 'CotoScraper',
    # UK
    'TescoScraper', 'SainsburysScraper', 'ASDASScraper', 'MorrisonsScraper', 
    'WaitroseScraper', 'IcelandScraper',
    # Europe
    'CarrefourScraper',
    # Australia/NZ
    'WoolworthsScraper', 'ColesScraper', 'IGAScraper', 
    'CountdownScraper', 'PaknSaveScraper', 'NewWorldScraper',
    # Asia
    'FairPriceScraper', 'BigBazaarScraper', 'DMartScraper', 
    'AeonScraper', 'EMartScraper', 'LotteMartScraper',
    # China
    'FreshippoScraper', 'RTMartScraper', 'YonghuiScraper', 'WumartScraper',
    # Middle East & Turkey
    'LuluHypermarketScraper', 'SpinneysScraper', 'ChoithramsScraper',
    'MigrosTurkeyScraper', 'BIMScraper', 'A101Scraper',
    # Russia
    'MagnitScraper', 'X5RetailScraper', 'LentaScraper', 'PerekrestokScraper',
    # Africa
    'ShopriteScraper', 'PicknPayScraper', 'CheckersScraper', 'WoolworthsSAScraper',
]
