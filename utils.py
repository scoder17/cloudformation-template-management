def make_subnet_private(template, subnet_name):
    resources = template.get("Resources", {})

    subnet = resources.get(subnet_name)
    if subnet and subnet["Type"] == "AWS::EC2::Subnet":
        subnet["Properties"]["MapPublicIpOnLaunch"] = False
    else:
        raise ValueError(f"Subnet {subnet_name} not found or is not a valid Subnet resource.")

    associated_route_tables = []
    associations_to_delete = []

    for logical_id, resource in list(resources.items()):
        if resource["Type"] == "AWS::EC2::SubnetRouteTableAssociation":
            if resource["Properties"]["SubnetId"].get("Ref") == subnet_name:
                associated_route_tables.append(resource["Properties"]["RouteTableId"].get("Ref"))
                associations_to_delete.append(logical_id)

    for logical_id in associations_to_delete:
        del resources[logical_id]

    routes_to_remove = []
    for logical_id, resource in list(resources.items()):
        if resource["Type"] == "AWS::EC2::Route":
            props = resource.get("Properties", {})
            if (
                props.get("DestinationCidrBlock") == "0.0.0.0/0"
                and "GatewayId" in props
                and props.get("RouteTableId", {}).get("Ref") in associated_route_tables
            ):
                routes_to_remove.append(logical_id)

    for route in routes_to_remove:
        del resources[route]

    eip_name = f"{subnet_name}EIP"
    resources[eip_name] = {
        "Type": "AWS::EC2::EIP",
        "Properties": {
            "Domain": "vpc"
        }
    }

    public_subnet_id = None
    for res in resources.values():
        if res["Type"] == "AWS::EC2::Subnet":
            if res["Properties"].get("MapPublicIpOnLaunch") is True:
                public_subnet_id = res["Properties"]["Tags"][0]["Value"]
                break

    if not public_subnet_id:
        raise ValueError("No public subnet found for placing NAT Gateway.")

    natgw_name = f"{subnet_name}NATGateway"
    resources[natgw_name] = {
        "Type": "AWS::EC2::NatGateway",
        "Properties": {
            "AllocationId": {"Fn::GetAtt": [eip_name, "AllocationId"]},
            "SubnetId": {"Ref": public_subnet_id},
            "Tags": [{"Key": "Name", "Value": f"{subnet_name}-NAT"}]
        }
    }

    rt_name = f"{subnet_name}PrivateRouteTable"
    resources[rt_name] = {
        "Type": "AWS::EC2::RouteTable",
        "Properties": {
            "VpcId": subnet["Properties"]["VpcId"],
            "Tags": [{"Key": "Name", "Value": f"{subnet_name}-PrivateRT"}]
        }
    }

    nat_route_name = f"{subnet_name}NatRoute"
    resources[nat_route_name] = {
        "Type": "AWS::EC2::Route",
        "Properties": {
            "RouteTableId": {"Ref": rt_name},
            "DestinationCidrBlock": "0.0.0.0/0",
            "NatGatewayId": {"Ref": natgw_name}
        }
    }

    assoc_name = f"{subnet_name}PrivateAssociation"
    resources[assoc_name] = {
        "Type": "AWS::EC2::SubnetRouteTableAssociation",
        "Properties": {
            "SubnetId": {"Ref": subnet_name},
            "RouteTableId": {"Ref": rt_name}
        }
    }

    return template