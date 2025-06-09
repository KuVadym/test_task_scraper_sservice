import asyncio
import hashlib
import inspect
import html
import os
from pathlib import Path
import re
import time
from typing import Literal
from api.dto import ProductDTO
from poshmark._browser_manager import BrowserManager, ErrorType
from local_db.crud import create_product, create_user, get_user_by_name
from local_db.models import Product, User
from random import randint
from pathlib import Path
import traceback
from accounts_api.connector import APIConnector





def normal_time(epoche):
    if epoche > 60:
        minutes = int(epoche // 60)
        seconds = int(epoche % 60)
    else:
        minutes = 0
        seconds = int(epoche)
    return f'{minutes} минут, {seconds} секунд'



class PoshmarkListing(BrowserManager):
    


    async def _again_to_listing(self):
        try:
            nav = self.page.locator('nav.header--scrollable')
            await nav.locator('a[data-et-name="sell"]').click()
            await asyncio.sleep(self.timeout_load)
            await self.page.wait_for_load_state('networkidle', timeout=300000)

        except Exception as ex:
            current_url = self.page.url
            
            current_func = inspect.currentframe().f_code.co_name
            self.log.exception(f'[{current_func}] current url: {current_url}', ex)
            await self.goto_page('https://poshmark.com/create-listing')
        
        finally:
            if not self.user:


                await self.save_cookies()

    async def _chec_url(self):
        if not (self.page.url == 'https://poshmark.com/create-listing' or 'https://poshmark.com/create-listing' in self.page.url):
            await self._again_to_listing()
            return True
        
    async def __upload_photos(self, photo_pathes):
        try:
            pathes = [str(Path(os.getcwd() + img_path).resolve()) for img_path in photo_pathes]
            await self.page.locator('#img-file-input').set_input_files(pathes)
            await asyncio.sleep(self.timeout_user + 2)
            image_modal = self.page.locator('.modal__body.listing-editor__image-modal').locator('xpath=..')
            await image_modal.locator('button[data-et-name="apply"]').click()
            
            await asyncio.sleep(self.timeout_user + randint(5, 15))
            return True
            
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)


    async def __download_photo(self, item: ProductDTO):
        photo_urls = set(item.images)
        photo_path = []
        tasks = []
        for photo_url in photo_urls:
            folder = os.path.join(os.getcwd(), 'photo', item.product_sku)
            os.makedirs(folder, exist_ok=True)

            name = hashlib.md5(photo_url.encode()).hexdigest()
            #duble hash
            name = hashlib.md5(name.encode()).hexdigest()
            endwith_ = photo_url.split('.')[-1]
            if endwith_.lower() in ['png', 'jpeg', 'jpg', 'bmp']:
                # path_ = os.path.join(folder, f'photo_{name}.{endwith_}')
                path_ = os.path.join(folder, f'photo_{name}.png')
            else:
                path_ = os.path.join(folder, f'{name}.png')
            photo_path.append(path_.split(os.getcwd())[1])
            tasks.append(self.download_image(photo_url, path_))
        await asyncio.gather(*tasks)
        return photo_path


    async def __fill_title(self, title: str):
        try:
            await self.page.get_by_placeholder("What are you selling? (required)").fill(title)
            await asyncio.sleep(self.timeout_user + randint(5,10))
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)


    async def __fill_description(self, description: str):
        try:
            description_clean = html.unescape(description)
            await self.page.get_by_placeholder("Describe it! (required)").fill(description_clean)
            await asyncio.sleep(self.timeout_user + randint(5,10))
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)
  

    async def __choise_category(self, item: ProductDTO): ## TODO fix category later
        try:
            uls = self.page.locator('.ws--nowrap > ul:nth-child(1)')

            category_drop = self.page.locator('[menuclass="ws--nowrap"]')
            maint_drop = uls.locator('xpath=..')

            await self.page.get_by_text('Select Category').click()
            main_c, aditional_c, sub_category = item.poshmark_category
            
            lis = (await uls.locator('li').all())[1:]
            names = list(map(lambda x: x.strip().lower(), await asyncio.gather(*[elem.text_content() for elem in lis])))
            category_dict = dict(zip(names, lis))

            await category_dict[main_c].click()
            await asyncio.sleep(randint(1,3))

            aditional_lis = await uls.locator('xpath=..').locator('li > div.p--l--7').all()
            aditional_names = list(map(lambda x: x.strip().lower(), await asyncio.gather(*[elem.text_content() for elem in aditional_lis])))
            aditional_category_dict = dict(zip(aditional_names, aditional_lis))

            await aditional_category_dict[aditional_c].click()
            await asyncio.sleep(randint(1,3))
            if not sub_category:
                return True
            sub_lis = await self.page.locator('div[class="dropdown form__text--select d--b"]', has_text='Select Subcategory (optional)').locator('li').all()
            sub_names = list(map(lambda x: x.strip().lower(), await asyncio.gather(*[elem.text_content() for elem in sub_lis])))
            sub_dict = dict(zip(sub_names, sub_lis))
            if sub_category in sub_dict:
                await sub_dict[sub_category].click()
                await asyncio.sleep(randint(1,3))
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)


    async def __get_poshmark_size_dict(self):
        drop_down = self.page.locator('[selectortestlocator="size"]')
        if not await drop_down.get_attribute('expandedoveridestate'):
            await self.page.locator('[data-test="size"]').click()
            await asyncio.sleep(self.timeout_user + 2)
        lis = await drop_down.locator('.p--3').locator('li').all()
        names = list(map(lambda x: x.strip().lower(), await asyncio.gather(*[elem.text_content() for elem in lis])))

        sizes_dict = dict(zip(names, lis))
        return names, sizes_dict

    async def __fill_size(self, size: str|list):
        size = [s.strip().lower() for s in size]
        print(size)
        async def write_custom_size(drop_down, size_list):
            for i, size_str in enumerate(size_list):
                if i == 0:
                    await drop_down.get_by_text('Custom').click()

                await drop_down.locator(f'#customSizeInput{i}').fill(size_str)

                if i < len(size_list) - 1:
                    await drop_down.get_by_role('button', name='Save').click()
                    if await drop_down.locator(
                            'div.d--fl.ai--c.cursor--pointer:has-text("Add another size")').is_visible():
                        print("Element is visible")
                    else:
                        print("Element is not visible")
                    # await drop_down.locator('div.d--fl.ai--c.cursor--pointer:has-text("Add another size")').wait_for(state="visible")
                    await drop_down.locator('div.d--fl.ai--c.cursor--pointer:has-text("Add another size")').click()
                else:
                    await drop_down.get_by_role('button', name='Save').click()
                    await drop_down.get_by_role('button', name='Done').click()



        try:
                       
            drop_down = self.page.locator('[selectortestlocator="size"]')
            if isinstance(size, list):
                await self.page.locator('[data-et-prop-content="multi"]').click()
                await asyncio.sleep(self.timeout_user + 3)

            names, sizes_dict = await self.__get_poshmark_size_dict()
            names.remove("save")
            if isinstance(size, list):
                size_intersection = set(names).intersection(list(filter(lambda x: x.strip().lower(), size)))
                if size_intersection:
                    if len(size_intersection) == 1 and len(names) == 1 and 'one size' in size_intersection:
                        await drop_down.get_by_role('button', name='Done').click()
                        return True
                    for inter in size_intersection:
                        await sizes_dict[inter].click()
                        await asyncio.sleep(self.timeout_user + 1)
                    await drop_down.get_by_role('button', name='Done').click()
                    return True
                else:

                    await write_custom_size(drop_down, size_list=size)
                    return True
            else:
                if size in names:
                    await sizes_dict[size].click()
                    return True
                else:
                    await write_custom_size(drop_down, size_list=size)


        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)


    async def __click_yes_nwt(self):
        try:
            await self.page.locator('[data-et-name="nwt_yes"]').click()
            await self.page.locator('.m--t--5').get_by_role('button', name='No').click()
            return True

        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)
        
    async def __click_no_nwt(self):
        try:
            await self.page.locator('[data-et-name="nwt_no"]').click()
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)
        
    async def __fill_brand(self, brand: str):
        try:
            await self.page.get_by_placeholder("Enter the Brand/Designer").fill(brand)
            return True

        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)
        
    async def __fill_color(self, itm_color: str|list|None):
        try:
            if itm_color == None:
                return True
            colors = await self.page.locator('.color__circle--large').all()
            lis = [color.locator('xpath=../..') for color in colors]
            names = list(map(
                lambda x: x.strip().lower(),
                await asyncio.gather(*[li.text_content() for li in lis])
            ))
            colors_dict = dict(zip(names, lis))
            print(colors_dict)

            if isinstance(itm_color, list):
                await self.page.locator('[data-et-name="color"]').locator('xpath=..').click()
                for requested_color in itm_color[:2]:
                    requested_color = requested_color.strip().lower()
                    if requested_color in colors_dict:
                        
                        await asyncio.sleep(self.timeout_user + 1)
                        await colors_dict[requested_color].click()
                        print(colors_dict[requested_color])
                        # Повторный сбор элементов для следующего клика
                        colors = await self.page.locator('.color__circle--large').all()
                        lis = [color.locator('xpath=../..') for color in colors]
                        names = list(map(
                            lambda x: x.strip().lower(),
                            await asyncio.gather(*[li.text_content() for li in lis])
                            ))
                        colors_dict = dict(zip(names, lis))
                    else:
                        self.log.info(f"Color '{requested_color}' not found on page")
            else:
                item_color_ = itm_color.strip().lower()
                inner_color = [x  for x in names if x in item_color_] 
                if not inner_color:
                    return True
                await self.page.locator('[data-et-name="color"]').locator('xpath=..').click()
                for color_ in inner_color[:2]:
                    await asyncio.sleep(self.timeout_user + 1)
                    await colors_dict[color_].click()

            await self.page.locator('[data-et-name="color"]').click()
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    """data-vv-name="style-tag-input"""
    async def __fill_tags(self, custom_tags):
        try:
            for tag in custom_tags[:3]:  # Ограничиваемся первыми тремя тегами
                await self.page.fill('input[data-vv-name="style-tag-input"]', tag)
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(self.timeout_user + 1)

            # await self.page.locator('input[data-vv-name="style-tag-input"]').click()
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

        
    async def __fill_price(self, price: str|int|float, LAP: int, OAP: int, discount: bool):
        try:

            if isinstance(price, str):
                cleaned_price = re.sub(r'[^0-9.]', '', price).split('.')[0]
                price = int(cleaned_price)
            if isinstance(price, float):
                price = int(price)
            listing_price = int(float(price) * (1 + (LAP / 100)))
            if discount:
                origin_price = int(float(price) * (1 + (OAP / 100)))
            else:
                origin_price = 0
            await self.page.locator('input[data-vv-name="originalPrice"]').fill(str(origin_price))
            await asyncio.sleep(self.timeout_user + randint(5, 12))
            await self.page.locator('input[data-vv-name="listingPrice"]').fill(str(listing_price))
            await asyncio.sleep(self.timeout_user + randint(5, 12))
            listing_footer = self.page.locator('.listing-editor__toggle')
            if await self.page.locator('[class="listing-editor-toggle__body expand"]').count() == 0:
                await listing_footer.locator('a.listing-editor-toggle-link').click()
            await asyncio.sleep(self.timeout_user + randint(2, 12))
            await self.page.locator('input[data-vv-name="costPriceAmount"]').fill(str(price))
            return True
        
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

        
    async def __fill_sku(self, sku: str):
        try:
            listing_footer = self.page.locator('.listing-editor__toggle')
            if await self.page.locator('[class="listing-editor-toggle__body expand"]').count() == 0:
                await listing_footer.locator('a.listing-editor-toggle-link').click()
            await asyncio.sleep(self.timeout_user + randint(2, 6))
            await self.page.locator('input[data-vv-name="sku"]').fill(sku)
            await asyncio.sleep(self.timeout_user + randint(5,7))
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

        
    async def __choise_availability(self, availability: Literal['N', 'S', 'D'] = 'N'):
        """
        N - Not for sale    \n
        S - For sale        \n
        D - Drop            \n
        """
        try:
                        
            ava_div = self.page.locator('[data-et-name="listingEditorAvailabilitySection"]')
            # if availability == 'S' and await ava_div.locator('.dropdown__selector--rotated').text_content() == 'For Sale':
            #     return
            await ava_div.locator('[items="available,not_for_sale,coming_soon"]').click()
            await asyncio.sleep(self.timeout_user + 2.1)
            if availability == "N":
                await self.page.locator('a[data-et-name="not_for_sale"]').click()
            elif availability == "S":
                await self.page.locator('a[data-et-name="available"]').click()
            elif availability == "D":
                await self.page.locator('a[data-et-name="coming_soon"]').click()
            else:
                await self.page.locator('a[data-et-name="not_for_sale"]').click()
                raise Exception(f' availability: {availability}')
                
            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def __close_ban_msg(self):
        modal = self.page.locator('[class="modal simple-modal modal--in modal--top modal--small"]')
        await modal.locator('[class="btn btn--primary"]').click()
    
    async def __ban_error_check(self) -> tuple[bool, ErrorType]:
        '''Return result of found error'''
        ban_text = 'Sorry! You cannot currently perform this request. Please reach out to Poshmark Support for assistance.'
        if await self.page.get_by_text(ban_text).count() > 0:
            self.log.exception('Baned msg')
            if self.test_mode:
                await self.__close_ban_msg()
                return False, ErrorType.NoError
            return True, ErrorType.BanError
        
        went_wrong = 'Something went wrong, Please try again later'
        if await self.page.get_by_text(went_wrong).count() > 0:
            self.log.exception('went wrong baner')
            return True, ErrorType.CancelPost
        
        return False, ErrorType.NoError
    

    async def __list_item(self, item: ProductDTO):
        try:
            await self.page.locator('button[data-et-name="next"]').click()
            await asyncio.sleep(self.timeout_user + 10)
            ban, bt = await self.__ban_error_check()
            if ban:
                self.last_error = bt
                self.log.error('Error baner after next btn')
                return False
            screen_shot_path = os.path.join(os.getcwd(), 'poshmark_result', f'{item.product_sku}.png')
            await self.page.wait_for_load_state('networkidle', timeout=120000)
            # await self.page.screenshot(path=screen_shot_path)
            await asyncio.sleep(self.timeout_user + randint(8, 17))
            await self.page.locator('[data-et-name="list"]').click()
            ban, bt = await self.__ban_error_check()
            if ban:
                self.last_error = bt
                self.log.error('Error baner after list btn')
                return False

            return True
        except Exception as ex:
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    def __posh_id(self):
        requests_list = self._requests.copy()
        for req in requests_list:
            if 'poshmark.com/vm-rest/users/' in req and '/seller_shipping_discounts/' in req:
                posh_id = req.split('object_id=')[-1].split('&app_')[0]
                return posh_id
            
            if 'https://poshmark.com/vm-rest/posts/' in req and '/media/scratch?app' in req  :
                posh_id = req.split('https://poshmark.com/vm-rest/posts/')[-1].split('/media/scratch?app')[0]
                return posh_id


    async def __wait_for_change_page(self, time_out: int = 30):
        ban, self.last_error = await self.__ban_error_check()
        start_wait_time = time.time()
        if ban:
            return False
        while self.page.url == 'https://poshmark.com/create-listing' or 'https://poshmark.com/create-listing' in self.page.url:
            await asyncio.sleep(self.timeout_user)
            if time.time() - start_wait_time > time_out:
                self.log.error('Wait for change page timeout')
                return False
        return True
    
    
    async def _reload_page(self, msg=None):
        if msg:
            self.log.info(f'Reload page by {msg}')
        self.log.debug(f'Reload page by error: {self.last_error.name}')
        await self.page.reload(timeout=90000)
        await asyncio.sleep(self.timeout_user + 6)
        self._error_processed = True
    


    
    async def _fill_item(
            self, 
            item: ProductDTO, 
            new_condition, 
            availability: Literal['N', 'S', 'D'] = 'N', 
            LAP: int = 5,
            OAP: int = 15,
            discount: bool = False,
            re_list_count: int = 0
            ):
        if re_list_count > 2:
            return False, None
        
        async def restart_listing():
            await self._reload_page()
            return await self._fill_item( 
                    item=item,
                    new_condition=new_condition, 
                    availability=availability, 
                    LAP = LAP,
                    OAP = OAP,
                    discount=discount,
                    re_list_count=re_list_count + 1,
                )
        
        try:
            photo_pathes = await self.__download_photo(item)
            await self._chec_url()
            await self.__ban_error_check()
            await asyncio.sleep(self.timeout_user + randint(2, 9))
            start_upload_ = time.time()
            
            upload_photos_res = await self.__upload_photos(photo_pathes)
        
            if not upload_photos_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            '''#################################################'''
            title_res = await self.__fill_title(item.title)
            if not title_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            '''#################################################'''
            description_res = await self.__fill_description(item.description)
            if not description_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            '''#################################################'''
            category_res = await self.__choise_category(item)
            if not category_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(2,10))
            '''#################################################'''
            if new_condition:
                nwt_res = await self.__click_yes_nwt()
            else:
                nwt_res = await self.__click_no_nwt()
            if not nwt_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(3,10))
            '''#################################################'''
            if item.brand:
                brand_res = await self.__fill_brand(item.brand)
                await asyncio.sleep(self.timeout_user + randint(3,12))

            size_res = await self.__fill_size(item.poshmark_sizes)
            if not size_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(4,12))
            '''#################################################'''
            self._requests.clear()

            if item.poshmark_color:
                color_res = await self.__fill_color(item.poshmark_color)
                await asyncio.sleep(self.timeout_user + randint(5,15))

            '''#################################################'''
            tags_res = await self.__fill_tags(['Western Boots', 'Women', 'Boots'])
            if not tags_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(3,12))

            price_res = await self.__fill_price(item.price, LAP, OAP, discount)
            if not price_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(4,10))
            '''#################################################'''
            
            sku_res = await self.__fill_sku(item.product_sku)
    
            availability_res = await self.__choise_availability(availability)
            
            if not availability_res:
                self.last_error = ErrorType.WhileFillError
                return await restart_listing()
            await asyncio.sleep(self.timeout_user + randint(3,13))
            '''#################################################'''
            
            result_dict = {
                "photo": upload_photos_res,
                "title": title_res,
                "description": description_res,
                "category": category_res,
                "size": size_res,
                "nwt": nwt_res,
                # "brand": brand,
                "price": price_res,
                "availability": availability_res,
            }

            listing_result = await self.__list_item(item)
            future_product_id = self.__posh_id()
            
            if listing_result is False and self.last_error.value > 1:
                self.log.error('============[ GOT BAN MSG ]============')
                return False, None
            elif not listing_result and self.last_error == ErrorType.CancelPost:
                self.log.error(f'Error while post listing item {item.id}-{item.variant_color}')
                result,_ = await restart_listing()
                if not result:
                    return False, None
            elif not listing_result:
                return await restart_listing()
            elif not future_product_id:
                return await restart_listing()

            print(f'Времени на заполнение {item.product_sku}: {normal_time(time.time() - start_upload_)}, результат публикации {listing_result}')
            self.log.info(f'Времени на заполнение {item.product_sku}: {normal_time(time.time() - start_upload_)}, результат публикации {listing_result}')
            
            wait_ = await self.__wait_for_change_page(time_out=90)
            if not wait_:
                await self._reload_page('no change page')
            return True, future_product_id         


        except Exception as ex:
            item_to_str = {
            "photo": item.images,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "posh_category": item.poshmark_category,
            "size": item.poshmark_sizes,
            "nwt": new_condition,
            # "brand": None,
            "price": item.price,
            "availability": availability,
            'color': item.variant_color
            }
            self.log.debug(f'item: {item_to_str}')
            current_func = inspect.currentframe().f_code.co_name
            exc_info = traceback.format_exception_only(type(ex), ex)
            short_traceback = ''.join(traceback.format_tb(ex.__traceback__, limit=3))  
            short_exc_info = ''.join(exc_info[0].split('attempt #2')[0]) 
            error_msg = f"[{current_func}] Exception: {short_exc_info}\nTraceback: {short_traceback}"
            self.log.error(error_msg)

    async def fill_items(
            self,
            user_id,
            items: list[ProductDTO],
            availability: Literal['N', 'S', 'D'] = 'N',
            new_condition: bool = False,
            listing_addit_percent: int = 5,
            origin_addit_percent: int = 15,
            discount: bool = False,
            ):
        """
        Filling the store with items
            items - list of items
            availability - type of listing
                N - Not for sale    |
                S - For sale        |
                D - Drop            
            new_condition: bool - condition of the item
            listing_addit_percent: int - markup on the listing price
            origin_addit_percent: int - markup on the original price
        """
        for item in items:
            self.log.info(f'Start listing items [{self.__class__.__name__}.fill_items]')
            self.log.debug(f'item count: {len(items)}, availability:{availability}, new_condition:{new_condition}, LAP/OAP:{listing_addit_percent}/{origin_addit_percent}')
            listing_result, future_product_id = await self._fill_item(
                item=item, 
                availability=availability, 
                new_condition=new_condition,
                LAP=listing_addit_percent,
                OAP=origin_addit_percent,
                discount=discount,
                )
            self.count += 1
            if listing_result:
                product_data = {
                    "id_in_shop": future_product_id,
                    "edit_url": f'https://poshmark.com/edit-listing/{future_product_id}',
                    "sku": item.product_sku,
                    "api_id": item.id,
                    "variant_color": item.variant_color,
                    "variant_ids": item.variant_ids,
                    "user_id": user_id,
                    "user_name": self.user.name,
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "posh_category": item.poshmark_category,
                    "size": item.poshmark_sizes,
                    "price": item.price,
                    "availability": availability,
                    "nwt": new_condition,
                    "color": item.poshmark_color,
                    "images": item.images
                }

                product_dict = {
                    "item_id": future_product_id,
                    "title": item.title,
                    "api_id": item.id,
                    "item_url": product_data["edit_url"],
                    "original_site_price": int(float(item.price) * (1 + (origin_addit_percent / 100))) if discount else 0,
                    "listing_price": int(float(item.price) * (1 + (listing_addit_percent / 100))),
                    "multi_item": 'True' if len(item.poshmark_sizes) > 1 else 'False',
                    "status": availability,
                    "user_id": user_id,
                    "sku": item.product_sku,  # Добавлено поле SKU
                    "variants": []
                }
                colors = item.poshmark_color or []
                sizes = item.poshmark_sizes or []

                if len(colors) == 0:
                    colors = [None]  # Если нет цветов, передаем пустой список

                if len(sizes) == 0:
                    sizes = [None]  # Если нет размеров, передаем пустой список

                # Генерируем варианты для каждого цвета и размера
                for color in colors:
                    for size in sizes:
                        variant_dict = {
                            "price_adjustment": 0,
                            "quantity": "",
                        }
                        if color:
                            variant_dict['color'] = color
                        if size:
                            variant_dict['size'] = size
                        product_dict['variants'].append(variant_dict)
                   
                api = APIConnector(base_url="http://fastapi_app:8093")
                api.create_products_bulk([product_dict])
                self.log.info(f'Save info about listed item: {future_product_id}')
            else:
                self.log.info(f'Ban')
                break
            await self.save_cookies()







