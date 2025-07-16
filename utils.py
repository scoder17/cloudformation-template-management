def make_subnet_private(template):
    resources = template.get('Resources', {})
    for key, res in resources.items():
        if res['Type'] == 'AWS::EC2::Subnet':
            props = res.get('Properties', {})
            props['MapPublicIpOnLaunch'] = False
    return template