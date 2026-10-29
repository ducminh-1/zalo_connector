--
UPDATE zalo_oa
   SET access_token = '',
       state = 'draft',
       access_token_expired_date = NULL,
       refresh_token = NULL,
       refresh_token_expired_date = NULL,
       app_id = '',
       secret_key = '',
       auth_code = '',
       code = '',
       zalo_oa_id = '',
       link_callback_url = '';

UPDATE res_company
   SET zalo_oa_id = NULL,
       zns_rating_template_id = NULL;
