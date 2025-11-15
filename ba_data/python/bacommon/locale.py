# Released under the MIT License. See LICENSE for details.
#
"""Functionality for wrangling locale info."""

from __future__ import annotations

import logging
from enum import Enum
from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, assert_never, assert_type

if TYPE_CHECKING:
    pass


class Locale(Enum):
    """A distinct grouping of language, cultural norms, etc.

    This list of locales is considered 'sacred' - we assume any values
    (and associated long values) added here remain in use out in the
    wild indefinitely. If a locale is superseded by a newer or more
    specific one, the new locale should be added and both new and old
    should map to the same :class:`LocaleResolved`.
    """

    # Locale values are not iso codes or anything specific; just
    # abbreviated English strings intended to be recognizable. In cases
    # where space is unimportant or humans might be writing these, go
    # with long-values which .

    ENGLISH = 'eng'
    PORTUGUESE_BRAZIL = 'prtg_brz'

    # Note: We use if-statement chains here so we can use assert_never()
    # to ensure we cover all existing values. But we cache lookups so
    # that we only have to go through those long if-statement chains
    # once per enum value.

    @cached_property
    def long_value(self) -> str:
        """A longer more human readable alternative to value.

        Like the regular enum values, these values will never change and
        can be used for persistent storage/etc.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        cls = type(self)

        if self is cls.ENGLISH:
            return 'English'
        if self is cls.PORTUGUESE_BRAZIL:
            return 'PortugueseBrazil'

        # Make sure we've covered all cases.
        assert_never(self)

    @classmethod
    def from_long_value(cls, value: str) -> Locale:
        """Given a long value, return a Locale."""

        # Build a map of long-values to locales on demand.
        storekey = '_from_long_value'
        fromvals: dict[str, Locale] | None = getattr(cls, storekey, None)
        if fromvals is None:
            fromvals = {val.long_value: val for val in cls}
            setattr(cls, storekey, fromvals)

        try:
            return fromvals[value]
        except KeyError as exc:
            raise ValueError(f'Invalid long value "{value}"') from exc

    @cached_property
    def description(self) -> str:
        """A human readable description for the locale.

        Intended as instructions to humans or AI for translating. For
        most locales this is simply the language name, but for special
        ones like pirate-speak it may include instructions.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        cls = type(self)

        if self is cls.ENGLISH:
            return 'English'
        if self is cls.PORTUGUESE_BRAZIL:
            return 'Portuguese (Brazil)'
        # Make sure we've covered all cases.
        assert_never(self)

    @cached_property
    def resolved(self) -> LocaleResolved:
        """Return the associated resolved locale."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        cls = type(self)
        R = LocaleResolved

        if self is cls.ENGLISH:
            return R.ENGLISH
        if self is cls.PORTUGUESE_BRAZIL or self is cls.PORTUGUESE:
            return R.PORTUGUESE_BRAZIL

        # Make sure we're covering all cases.
        assert_never(self)


class LocaleResolved(Enum):
    """A resolved :class:`Locale` for use in logic.

    These values should never be stored or transmitted and should always
    come from resolving a :class:`Locale` which *can* be
    stored/transmitted. This gives us the freedom to revise this list as
    needed to keep our actual list of implemented resolved-locales as
    trim as possible.
    """

    ENGLISH = 'eng'
    PORTUGUESE_BRAZIL = 'prtg_brz'

    # Note: We use if-statement chains here so we can use assert_never()
    # to ensure we cover all existing values. But we cache lookups so
    # that we only have to go through those long if-statement chains
    # once per enum value.

    @cached_property
    def locale(self) -> Locale:
        """Return a locale that resolves to this resolved locale.

        In some cases, such as when presenting locale options to the
        user, it makes sense to iterate over resolved locale values, as
        regular locales may include obsolete or redundant values. When
        storing locale values to disk or transmitting them, however, it
        is important to use plain locales. This method can be used to
        get back to a plain locale from a resolved one.
        """
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        cls = type(self)

        if self is cls.ENGLISH:
            return Locale.ENGLISH
        if self is cls.PORTUGUESE_BRAZIL:
            return Locale.PORTUGUESE_BRAZIL

        # Make sure we're covering all cases.
        assert_never(self)

    @cached_property
    def tag(self) -> str:
        """An IETF BCP 47 tag for this locale.

        This is often simply a language code ('en') but may in some
        cases include the country ('pt-BR') or script ('zh-Hans').
        Locales which are not "real" will include an 'x' in the middle
        ('en-x-pirate').
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        cls = type(self)

        val: str | None = None

        if self is cls.ENGLISH:
            val = 'en'
        elif self is cls.PORTUGUESE_BRAZIL:
            val = 'pt-BR'
        else:
            # Make sure we cover all cases.
            assert_never(self)

        assert_type(val, str)

        # Sanity check: the tag we return should lead back to us if we
        # use it to get a Locale and then resolve that Locale. Make some
        # noise if not so we can fix it.
        lrcheck = LocaleResolved.from_tag(val)
        if lrcheck is not self:
            logging.warning(
                'LocaleResolved.from_tag().resolved for "%s" yielded %s;'
                ' expected %s.',
                val,
                lrcheck.name,
                self.name,
            )

        return val

    @classmethod
    @lru_cache(maxsize=128)
    def from_tag(cls, tag: str) -> LocaleResolved:
        """Return a locale for a given string tag.

        Tags can be provided in BCP 47 form ('en-US') or POSIX locale
        string form ('en_US.UTF-8').
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-return-statements

        # POSIX locale strings can contain a dot followed by an
        # encoding. Strip that off.
        tag2 = tag.split('.')[0]

        # Normalize things to lowercase and underscores (we should see
        # 'zh_HANT' and 'zh-Hant' as the same).
        bits = [bit.lower() for bit in tag2.replace('-', '_').split('_')]

        if not bits or not bits[0]:
            raise ValueError(f'Invalid tag "{tag}".')

        lang = bits[0]
        extras = bits[1:]

        if lang == 'en':
            if 'x' in extras and 'pirate' in extras:
                return cls.PIRATE_SPEAK
            if 'x' in extras and 'gibberish' in extras:
                return cls.GIBBERISH
            return cls.ENGLISH
        if lang == 'pt':
            # With no extras, default to Brazil.
            if not extras or 'br' in extras:
                return cls.PORTUGUESE_BRAZIL
            if any(
                val in extras
                for val in ['pt', 'ao', 'mz', 'tl', 'cv', 'gw', 'st']
            ):
                return cls.PORTUGUESE_PORTUGAL

            # Make noise if we come across something unexpected so we
            # can add it.
            fallback = cls.PORTUGUESE_BRAZIL
            logging.warning(
                '%s: Unknown Portuguese tag variant "%s"; returning %s.',
                cls.__name__,
                tag,
                fallback.name,
            )
            return fallback

        # Make noise if we come across something unexpected so we can
        # add it.
        fallback = cls.ENGLISH
        logging.warning(
            '%s: Unknown tag "%s"; returning %s.',
            cls.__name__,
            tag,
            fallback.name,
        )
        return fallback
