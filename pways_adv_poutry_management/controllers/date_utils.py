from datetime import datetime, timedelta


def parse_datetime_param(datetime_str):
    """Parse datetime string with multiple format support"""
    if not datetime_str or not isinstance(datetime_str, str):
        return None

    formats = [
        '%Y-%m-%d %H:%M:%S.%f',  # With microseconds
        '%Y-%m-%d %H:%M:%S',  # Without microseconds
        '%Y-%m-%d',  # Date only
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None


def get_date_range(env, default_days=30):
    """Get date range from system parameters with fallback"""
    Param = env['ir.config_parameter'].sudo()
    start_date_str = Param.get_param('pways_adv_poutry_management.start_date')
    end_date_str = Param.get_param('pways_adv_poutry_management.end_date')

    start_date = parse_datetime_param(start_date_str)
    end_date = parse_datetime_param(end_date_str)

    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=default_days)

    return start_date, end_date