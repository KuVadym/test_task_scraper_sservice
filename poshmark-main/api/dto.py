from cgi import print_arguments
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import re

from zmq import Enum



color_mapping = {
    'red': ('red',), 'pink': ('pink',), 'yellow': ('yellow',),
    'orange': ('orange',), 'green': ('green',), 'blue': ('blue',),
    'purple': ('purple',), 'gold': ('gold',), 'silver': ('silver',),
    'black': ('black',), 'gray': ('gray',), 'white': ('white',),
    'cream': ('cream',), 'tan': ('tan',), 'brown': ('brown',)
}


def get_poshmark_colors(color):
    # Разбиваем строку цвета на элементы, учитывая различные разделители
    colors = re.split(r'[\/,&\s]+', color.lower())
    result_colors = []

    for col in colors:
        # Проверяем каждый цвет и добавляем его аналог из маппинга
        for m_color in color_mapping:
            if m_color in col:
                mapped_colors = color_mapping[m_color]
                for mapped_color in mapped_colors:
                    if mapped_color not in result_colors:
                        result_colors.append(mapped_color)
                        # Ограничиваем список тремя цветами
                        if len(result_colors) == 2:
                            return tuple(result_colors)  # Возвращаем кортеж

    # Если не найдено соответствие или цвет не попал в маппинг
    if not result_colors:
        return None
    
    return tuple(result_colors)  # Возвращаем кортеж


def boot_barn_sizes(size_str):


    pattern = re.compile(r'[DEM]{1,2}_(\d+)(?:\s*1/2)?')
    # Функция для конвертации размеров
    def convert_size(match):
        size = match.group(1)
        if '1/2' in match.group(0):
            return str(float(size) + 0.5)
        else:
            return str(float(size))
    # Извлечение и конвертация размеров
    sizes = [convert_size(match) for match in pattern.finditer(size_str)]
    return sizes

# class OptionType(Enum):
#     Size = 'size'
#     Color = 'color'
#     Url = 'url'




@dataclass
class VariantDTO:
    quantity: int
    price_adjustment: int
    variant_images: list = field(default_factory=list)
    url: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    id: Optional[int] = None




@dataclass
class ProductDTO:
    id: int
    title: str
    description: str
    updated_at: str
    created_at: str
    platform: dict
    category: dict
    images: List[str]
    price: int
    product_sku: str
    variants: List[VariantDTO]
    url: str
    brand: Optional[str] = ''
    
    variant_color: Optional[str] = ''
    poshmark_category: Optional[List] = field(default_factory=list)
    other_data: Dict = field(default_factory=dict)
    api_dict: Dict = field(default_factory=dict)
    poshmark_sizes: List = field(default_factory=list)
    poshmark_color: List = field(default_factory=list)
    variant_ids: List = field(default_factory=list)

    def __post_init__(self):
        if self.platform['name'] == 'bootbarn':
            try:
                color_dict = {}
                added_colors = set()
                self.other_data['color_dict'] = color_dict
                for inx, variant in enumerate(self.variants):
                    variant_color = variant.color
                    poshmark_colors = get_poshmark_colors(variant_color)

                    if not poshmark_colors:
                        if variant_color not in added_colors:
                            # Если цвет не найден в Poshmark и еще не добавлен в title
                            self.title += f" {variant_color}"
                            self.description += f"\nColor: {variant_color}"
                            added_colors.add(variant_color)
                    if not variant_color in color_dict:
                        color_dict[variant_color] = {
                                    'sizes_str': '',
                                    'sizes':None,
                                    'images':[] if inx != 0 else deepcopy(self.images),
                                    'price': self.price + variant.price_adjustment,
                                    'poshmark_color':poshmark_colors,
                                    'variant_ids': [variant.id],
                                    'variant_skus': []
                                    }
                    color_ = color_dict[variant_color]
                    if variant.size: color_['sizes_str'] += f'_{variant.size}'
                    if variant.variant_images: color_['images'] +=  variant.variant_images
                    if variant.id not in  color_['variant_ids']:
                        color_['variant_ids'].append(variant.id )
                for color, variant_dict in color_dict.items():
                    if 'shoes' in self.poshmark_category:
                        if '1/2' in variant_dict['sizes_str']:
                            color_dict[color]['sizes'] = list(set(boot_barn_sizes(variant_dict['sizes_str'])))
                        else:
                            pattern = r'\d+\.?\d*'
                            color_dict[color]['sizes'] = list(set(re.findall(pattern, variant_dict['sizes_str'])))
                    else:
                        # print(self.url)
                        # print(variant_dict['sizes_str'])
                        color_dict[color]['sizes'] = [x for x in list(set(variant_dict['sizes_str'].split('_'))) if x]
            except Exception as ex:
                print(ex)
        else:
            pass
# @dataclass
# class ProductDTO:
#     id: int
#     title: str
#     description: str
#     updated_at: str
#     created_at: str
#     platform: dict
#     category: dict
#     images: List[str]
#     price: int
#     product_sku: str
#     variants: List[VariantDTO]
#     url: str
#     brand: Optional[str] = ''
    
#     variant_color: Optional[str] = ''
#     poshmark_category: Optional[List] = field(default_factory=list)
#     other_data: Dict = field(default_factory=dict)
#     api_dict: Dict = field(default_factory=dict)
#     poshmark_sizes: List = field(default_factory=list)
#     poshmark_color: List = field(default_factory=list)
#     variant_ids: List = field(default_factory=list)

#     def __post_init__(self):
#         if self.platform['name'] == 'bootbarn':

#             try:
#                 color_dict = {}
#                 self.other_data['color_dict'] = color_dict
#                 for inx, variant in enumerate(self.variants):
#                     variant_color = variant.color
#                     if not variant_color in color_dict:
#                         color_dict[variant_color] = {
#                                     'sizes_str': '',
#                                     'sizes':None,
#                                     'images':[] if inx != 0 else deepcopy(self.images),
#                                     'price': self.price + variant.price_adjustment,
#                                     'poshmark_color':get_poshmark_colors(variant.color),
#                                     'variant_ids': [variant.id],
#                                     'variant_skus': []
#                                     }
#                     color_ = color_dict[variant_color]
#                     if variant.size: color_['sizes_str'] += f'_{variant.size}'
#                     if variant.variant_images: color_['images'] +=  variant.variant_images
#                     if variant.id not in  color_['variant_ids']:
#                         color_['variant_ids'].append(variant.id )
#                 for color, variant_dict in color_dict.items():
#                     if not self.poshmark_category:
#                         return
#                     if 'shoes' in self.poshmark_category:
#                         if '1/2' in variant_dict['sizes_str']:
#                             color_dict[color]['sizes'] = list(set(boot_barn_sizes(variant_dict['sizes_str'])))
#                         else:
#                             pattern = r'\d+\.?\d*'
#                             color_dict[color]['sizes'] = list(set(re.findall(pattern, variant_dict['sizes_str'])))
#                     elif re.search(r'\b(x{0,2}s|m|l|x{1,3}l)\b', variant_dict['sizes_str'].lower().replace('_', ' ')):
#                         self.poshmark_sizes = re.findall(r'\b(x{0,2}s|m|l|x{1,3}l)\b', variant_dict['sizes_str'].lower().replace('_', ' '))
                    
#                     elif 'jeans' in self.poshmark_category:
#                         self.poshmark_sizes = [f'us waist {x.split(' ')[0]}' for x in variant_dict['sizes_str'].lower().split('_')]
#                     else:
#                         sizes = [x for x in list(set(variant_dict['sizes_str'].lower().split('_'))) if x]
#                         if sizes:
#                             if 'one size' in sizes:
#                                 self.poshmark_sizes  = None
#                                 return
#                         print(variant_dict['sizes_str'], print(self.url))
#                         self.poshmark_sizes  = [x for x in list(set(variant_dict['sizes_str'].lower().split('_'))) if x]
        
#             except Exception as ex:
#                 print(ex)
#         elif self.platform['name'] == 'orvis':
#             try:
#                 color_dict = {}
#                 self.other_data['color_dict'] = color_dict
#                 for inx, variant in enumerate(self.variants):
#                     variant_color = variant.color
#                     if not variant_color in color_dict:
#                         color_dict[variant_color] = {
#                                     'sizes_str': '',
#                                     'sizes':None,
#                                     'images':[] if inx != 0 else deepcopy(self.images),
#                                     'price': self.price + variant.price_adjustment,
#                                     'poshmark_color':get_poshmark_colors(variant.color),
#                                     'variant_ids': [variant.id],
#                                     'variant_skus': []
#                                     }
#                     color_ = color_dict[variant_color]
#                     if variant.size: color_['sizes_str'] += f'_{variant.size}'
#                     if variant.variant_images: color_['images'] +=  variant.variant_images
#                     if variant.id not in  color_['variant_ids']:
#                         color_['variant_ids'].append(variant.id )
#                 for color, variant_dict in color_dict.items():
#                     if not self.poshmark_category:
#                         return
#                     if 'shoes' in self.poshmark_category:
#                         if '1/2' in variant_dict['sizes_str']:
#                             color_dict[color]['sizes'] = list(set(boot_barn_sizes(variant_dict['sizes_str'])))
#                         else:
#                             pattern = r'\d+\.?\d*'
#                             color_dict[color]['sizes'] = list(set(re.findall(pattern, variant_dict['sizes_str'])))
#                     elif re.search(r'\b(x{0,2}s|m|l|x{1,3}l)\b', variant_dict['sizes_str'].lower().replace('_', ' ')):
#                         self.poshmark_sizes = re.findall(r'\b(x{0,2}s|m|l|x{1,3}l)\b', variant_dict['sizes_str'].lower().replace('_', ' '))
                    
#                     elif 'jeans' in self.poshmark_category:
#                         self.poshmark_sizes = [f'us waist {x.split(' ')[0]}' for x in variant_dict['sizes_str'].lower().split('_')]
#                     else:
#                         sizes = [x for x in list(set(variant_dict['sizes_str'].lower().split('_'))) if x]
#                         if sizes:
#                             if 'one size' in sizes:
#                                 self.poshmark_sizes  = None
#                                 return
#                         print(variant_dict['sizes_str'], print(self.url))
#                         self.poshmark_sizes  = [x for x in list(set(variant_dict['sizes_str'].lower().split('_'))) if x]
        
#             except Exception as ex:
#                 print(ex)
#         else:
#             pass



@dataclass
class WebsiteDTO:
    name: str
    url: str
    id: Optional[int] = None

@dataclass
class CategoryDTO:
    name: str
    id: Optional[int] = None



