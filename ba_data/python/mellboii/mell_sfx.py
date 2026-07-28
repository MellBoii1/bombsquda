"""A module containing a single dict with SFX.
Useful for getting a shared instance of sounds."""
import bascenev1 as bs
class SoundFactory:
    """Wraps up sounds for a bunch of stuff."""
    _STORENAME = bs.storagename()
    
    def __init__(self):
        self.clash = bs.getsound('clash')
        self.turbo_death = bs.getsound('boo')
        self.attempt_parry = bs.getsound('attempt_parry')
        self.parry_success = bs.getsound('parried')
        self.hook_despawn = bs.getsound('swip')
        self.hook_throw = bs.getsound('hook_throw')
        self.horn_warningS = bs.getsound('s3kb2')
        self.horn_dangerS = bs.getsound('s3k50')
        self.horn_warningV = bs.getsound('HWARNING')
        self.horn_dangerV = bs.getsound('HDANGER')
        self.firework_launch_classic = bs.getsound('wackyplatform')
        self.firework_explode_classic = bs.getsound('retired')
        self.firework_launch = bs.getsound('firework_lit')
        self.firework_explode = bs.getsound('firework_explode')
        self.mortal_damage = bs.getsound('mortal_damage')
        self.mortal_damage_spike = bs.getsound('mortal_dmg_spike')
        self.survived_mortal_damage = bs.getsound('scoreOG')
        self.ok_item = bs.getsound('okitem')
        self.good_item = bs.getsound('gooditem')
        self.bad_item = bs.getsound('baditem')
        self.fireball_throw = bs.getsound('smb1_fireball')
        self.wiggle_start = bs.getsound('drumRollShort')
        self.super_pre = bs.getsound('pretrans')
        self.super_trans = bs.getsound('supertrans')
        self.spongebob_tick = bs.getsound('spongebob')
        self.spongebob_death = bs.getsound('spongebobdead')
        self.equip_metalcap = bs.getsound('metalcap')
        self.shotgun_shot = bs.getsound('shotgunshot')
        self.prowler = bs.getsound('theFinaleStart')
        self.blocktales_dodge = bs.getsound('BTdodge')
        self.blocktales_rating1 = bs.getsound('BTrating1')
        self.blocktales_rating2 = bs.getsound('BTrating2')
        self.blocktales_rating3 = bs.getsound('BTrating3')
        self.blocktales_rating4 = bs.getsound('BTrating4')
        self.blocktales_rating5 = bs.getsound('BTrating5')
        self.emeralds_drop = bs.getsound('ring_spill')
        self.party_blower = bs.getsound('party_blower')
        self.head_explosion = bs.getsound('party_blower')
        self.crit_bloody = bs.getsound('critBloody')
        self.crit = bs.getsound('criticalHit')
        self.cola_drink = bs.getsound('cola')
        self.heal = bs.getsound('heal')
        self.flight_refilled = bs.getsound('connected')
        self.tear_fire = (
            bs.getsound('tear_fire1'), 
            bs.getsound('tear_fire2'),
        )
        self.super_dash = bs.getsound('swordlunge')
        self.invincible_hit_sound = bs.getsound('block')
        self.critical_impact = bs.getsound('critical_impact')
        self.critical_impact_concrete = bs.getsound('critical_impact_concrete')
        self.tnt_break = bs.getsound('tnt_break')
        self.player_ragdoll_impact = (
            bs.getsound('ragdoll_impact1'),
            bs.getsound('ragdoll_impact2'),
            bs.getsound('ragdoll_impact3'),
        )
    
    @classmethod
    def get(cls):
        """Return the shared bs.SpazFactory, creating it if necessary."""
        # pylint: disable=cyclic-import
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = SoundFactory()
        assert isinstance(factory, SoundFactory)
        return factory