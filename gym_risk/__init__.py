from gym.envs.registration import register

register(
    id='Risk-v0',
    entry_point='gym_risk.envs:RiskEnv',
)

register(
    id='DraftingRisk-v0',
    entry_point='gym_risk.envs:DraftingRiskEnv',
)
