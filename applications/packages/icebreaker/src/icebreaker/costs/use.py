
def costs_local_spending_per_second(
    hardware_cost: float,
    expected_years: int
):
    expected_years_in_seconds = expected_years * 365 * 24 * 60 * 60
    spend_euros_per_second = hardware_cost/expected_years_in_seconds
    return spend_euros_per_second

def costs_csc_euros_per_billing_unit(
    package_billing_units: int,
    package_cost_euros: int
):
    euros_per_billing_unit = package_cost_euros/package_billing_units
    return euros_per_billing_unit

def costs_csc_cloud_spending_per_second(
    package_cost_euros: int,
    package_billing_units: int,
    spent_units_per_hour: int
):
    euros_per_billing_unit = costs_csc_euros_per_billing_unit(
        package_cost_euros = package_cost_euros,
        package_billing_units = package_billing_units
    )
    spent_units_per_second = spent_units_per_hour/(60*60)
    spent_euros_per_second = euros_per_billing_unit * spent_units_per_second
    return spent_euros_per_second
    
def costs_lumi_hpc_spending_per_second(
    euroes_per_cpu_node_hour: float,
    node_to_core_hour_ratio: int,
    used_cpu_core_hours: int
):
    spent_euroes_per_second = euroes_per_cpu_node_hour * (1/node_to_core_hour_ratio) * used_cpu_core_hours
    return spent_euroes_per_second
    