"""Objection Matrix — verbatim rebuttal scripts from the Master Objection Matrix document.

Rebuttal text is stored exactly as written in the source document.
{{CUSTOMER_NAME}} placeholders are substituted with the actual customer name by
query_objection_matrix() before the text is returned to the agent.
Category 14 Argument 1 was translated from Spanish to English (agent speaks English only).

Field names:
  - category         : human-readable label used as Argumentation_Used in CRM logs
  - trigger_keywords : keywords that help the agent identify this category
  - arguments        : list of {use_when, rebuttal} dicts (indexed from 1)

Each category has 1–4 arguments. Pass argument=1 (default) for the primary
rebuttal. Pass argument=2, 3, or 4 when the customer's context matches the
use_when description. When in doubt, always use argument=1.
"""

OBJECTION_MATRIX = {

    # ── Category 1: Too Expensive ─────────────────────────────────────────────
    "TOO_EXPENSIVE": {
        "category": "Too Expensive",
        "trigger_keywords": [
            "expensive", "costly", "a lot of money", "I don't have any money",
            "high price", "budget", "I can't afford it", "high bill", "very expensive",
        ],
        "arguments": [
            {
                "use_when": "Ideal if user mentions 'uncertainty' or 'forgetting to recharge'",
                "rebuttal": (
                    "I completely understand. The great thing about this plan is that it "
                    "replaces all your monthly top-ups with a single fixed payment, so you "
                    "won't have to worry about running out of credit unexpectedly. Plus, "
                    "you'll only pay a discounted promotional rate for the first few months, "
                    "and then the regular basic rate. It's a way to better manage your "
                    "expenses, doesn't it sound good?"
                ),
            },
            {
                "use_when": "Ideal if user says 'Prepaid is cheaper'",
                "rebuttal": (
                    "I understand your point, {{CUSTOMER_NAME}}. However, please note that "
                    "this promotional price guarantees you a large data allowance "
                    "indefinitely. If you try to use the same amount of data on a prepaid "
                    "plan, I assure you it would be much more expensive. It's an investment "
                    "for unrestricted browsing. What do you think?"
                ),
            },
            {
                "use_when": "Ideal if user is analytical or compares specs",
                "rebuttal": (
                    "If you divide the fixed monthly price by the included gigabytes we "
                    "give you, each Giga costs you a fraction of the cost. In prepaid, a "
                    "package of a few gigabytes is more expensive. It is the cheapest way "
                    "to navigate."
                ),
            },
            {
                "use_when": "Ideal if user says data runs out too fast",
                "rebuttal": (
                    "Has it happened to you that you buy a standard prepaid package and "
                    "before the month ends your data runs out? You have to make a small "
                    "emergency recharge. At the end of the month, you ended up spending a "
                    "much higher amount. With the plan, your bill is frozen at this "
                    "promotional rate."
                ),
            },
        ],
    },

    # ── Category 2: No Monthly Bill ───────────────────────────────────────────
    "NO_MONTHLY_BILL": {
        "category": "No Monthly Bill",
        "trigger_keywords": [
            "I don't want bills", "I don't like being in debt", "I don't want receipts",
            "I prefer to pay and that's it", "without monthly commitments",
            "I don't want commitment",
        ],
        "arguments": [
            {
                "use_when": "Use if user fears being 'Cut Off' or losing service",
                "rebuttal": (
                    "I understand your point, {{CUSTOMER_NAME}}. But think of it this way: "
                    "more than a bill, this is connectivity insurance. Even if you use up "
                    "all your data, you'll still be able to browse Facebook, WhatsApp, and "
                    "Instagram. That means you'll never, ever be disconnected, whereas with "
                    "prepaid plans, if you run out of data, your service ends immediately. "
                    "Wouldn't you like that peace of mind?"
                ),
            },
            {
                "use_when": "Use if user is focused on 'Saving Money'",
                "rebuttal": (
                    "You're looking for savings, and that's precisely why it's in your "
                    "best interest to switch today. We have a special welcome discount for "
                    "the first few months, so you'll end up paying less than you do now "
                    "with all those small top-ups, while receiving significantly more "
                    "content. It's real savings for your wallet, what do you think?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Effort' or 'Hassle of recharging'",
                "rebuttal": (
                    "Think about all the time you waste looking for a place to recharge or "
                    "dealing with the app every week. With the invoice, the service renews "
                    "automatically, and you can completely forget about lines or keeping "
                    "track of recharge tokens. It's more time and convenience for you. "
                    "Shall we activate this benefit now?"
                ),
            },
        ],
    },

    # ── Category 3: Prefer Prepaid Control ───────────────────────────────────
    "PREFER_PREPAID_CONTROL": {
        "category": "Prefer Prepaid Control",
        "trigger_keywords": [
            "I prefer prepaid", "that way I control my spending",
            "I don't want to go over my budget", "I decide when to recharge",
            "I like to have control", "control of consumption",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'Current Spending' or 'Saving'",
                "rebuttal": (
                    "It's funny, {{CUSTOMER_NAME}}, but sometimes with prepaid we spend "
                    "more without realizing it on frequent, small emergency top-ups. With "
                    "this fixed-price plan, you know exactly how much you'll pay each month "
                    "and receive plenty of data for unlimited browsing. It's much smarter "
                    "control for your money. Would you like to try it?"
                ),
            },
            {
                "use_when": "Use if user is focused on 'Cheapest Option'",
                "rebuttal": (
                    "I understand perfectly. You're careful with your spending, looking "
                    "for savings, and today the best way to save is right here: we're "
                    "giving you a special welcome discount for the first few months. "
                    "You'll pay less than the plan normally costs and receive much more "
                    "than with your current top-ups. Shall we activate this discount?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Convenience' or 'Avoiding expiration'",
                "rebuttal": (
                    "Real control means not having to worry about whether your plan expired "
                    "today or tomorrow, or having to go out and find a place to top up. "
                    "Here, your service renews automatically every month with the apps you "
                    "use most, so you're always connected and worry-free. How about we "
                    "help you manage it all for you?"
                ),
            },
        ],
    },

    # ── Category 4: Bad Past Experience ──────────────────────────────────────
    "BAD_PAST_EXPERIENCE": {
        "category": "Bad Past Experience",
        "trigger_keywords": [
            "bad experience", "I was robbed", "the service is bad",
            "I've already had problems", "I don't trust them", "I filed a complaint",
            "they overcharged me", "terrible service",
        ],
        "arguments": [
            {
                "use_when": "Use if user is emotionally frustrated or angry",
                "rebuttal": (
                    "I'm so sorry to hear that, {{CUSTOMER_NAME}}. We want you to know "
                    "that our priority today is to provide you with something much more "
                    "valuable and change that perception. Let's make this the last time "
                    "you feel bad about the company; we're here to show you that our "
                    "service has improved. Will you give us the opportunity to demonstrate "
                    "that with this benefit?"
                ),
            },
            {
                "use_when": "Use if user mentions technical issues or signal",
                "rebuttal": (
                    "I understand your frustration. By upgrading to postpaid, you're not "
                    "just signing up for a service; you're making a clear commitment to "
                    "the future. With this plan, you'll have access to the best available "
                    "technology and a much more stable and faster connection than with "
                    "prepaid. We want your experience to be seamless from now on. How "
                    "about we get started today?"
                ),
            },
            {
                "use_when": "Use if user mentions 'money issues' or 'overcharging'",
                "rebuttal": (
                    "I completely understand. With this change, we're precisely aiming to "
                    "save you the stress of having to claim for money you shouldn't have "
                    "to pay or for lost balances. Come to the security of Movistar: "
                    "you'll have a fixed bill, with no hidden charges, and with the welcome "
                    "promotional discount I mentioned. It's total transparency. "
                    "Shall I confirm the change?"
                ),
            },
        ],
    },

    # ── Category 5: No Commitment ─────────────────────────────────────────────
    "NO_COMMITMENT": {
        "category": "No Commitment",
        "trigger_keywords": [
            "I don't want contracts", "I don't want to be tied down",
            "to have permanence", "clauses", "a time commitment",
            "how long I have to stay", "penalties", "to be able to leave whenever I want",
        ],
        "arguments": [
            {
                "use_when": "Use if user is concerned about 'Future Changes'",
                "rebuttal": (
                    "I understand your concern, {{CUSTOMER_NAME}}. Flexibility today is "
                    "total: you do not sign an exclusivity contract for life. If tomorrow "
                    "you feel that you want to make any modification or change, you are "
                    "free to request it. The important thing is that today you start "
                    "enjoying the benefits. Is that okay with you?"
                ),
            },
            {
                "use_when": "Use if user fears 'Legal Ties' or 'Being Stuck'",
                "rebuttal": (
                    "This change is completely flexible. In fact, Movistar has eliminated "
                    "long-term contracts for these plans so you only stay with us for the "
                    "quality of service, not out of obligation. You have full control of "
                    "your line and your bill each month, with no strings attached. "
                    "Shall we activate the service under these conditions?"
                ),
            },
        ],
    },

    # ── Category 6: No Time ───────────────────────────────────────────────────
    "NO_TIME": {
        "category": "No Time",
        "trigger_keywords": [
            "I don't have time", "I'm busy", "I'm working", "call me later",
            "I'm driving", "I'm in a meeting", "don't delay", "hurry",
        ],
        "arguments": [
            {
                "use_when": "Use if user says 'I am busy' or 'Don't take long'",
                "rebuttal": (
                    "I understand, {{CUSTOMER_NAME}}, that's why I'm calling you today. "
                    "My job is to save you time and eliminate the worry of constant "
                    "top-ups. Switching from Prepaid to Postpaid with the exclusive "
                    "discount takes less than 2 minutes, with no paperwork and no need "
                    "to change your SIM card. Shall we get it sorted right away?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Hassle' or 'Valuable time'",
                "rebuttal": (
                    "Precisely because your time is valuable, the goal of this change is "
                    "to eliminate interruptions. There's nothing more frustrating than "
                    "running out of data mid-journey or in an emergency because you "
                    "haven't topped up. By switching to postpaid, your service is never "
                    "interrupted, and you gain time for what truly matters. "
                    "What do you think?"
                ),
            },
        ],
    },

    # ── Category 7: Satisfied with Recharges ─────────────────────────────────
    "SATISFIED_WITH_RECHARGES": {
        "category": "Satisfied With Recharges",
        "trigger_keywords": [
            "I'm fine like this", "I like prepaid", "I don't need anything else",
            "it works well for me", "I keep recharging", "I'm at ease like this",
            "I don't want to change", "the recharges last me a long time",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'saving' or 'it's enough for me'",
                "rebuttal": (
                    "I understand, {{CUSTOMER_NAME}}. Top-ups are convenient, but if we "
                    "add up those small top-ups over the month, you end up paying up to "
                    "30% more per gigabyte than a postpaid customer. With this offer, "
                    "we'll give you plenty of gigabytes for practically the same price "
                    "you're spending now, but with much more capacity. How about we "
                    "optimize your spending right away?"
                ),
            },
            {
                "use_when": "Use if user is focused on 'future value' or 'financing'",
                "rebuttal": (
                    "I completely understand. However, there's a benefit to postpaid that "
                    "prepaid doesn't offer: your punctuality with your payments will build "
                    "a positive credit history. In a few months, this will help you finance "
                    "a high-end device with Movistar or even assist you with other "
                    "important financial transactions. It's an investment in your future. "
                    "Would you like to start building that credit history today?"
                ),
            },
        ],
    },

    # ── Category 8: Only Uses Minutes ────────────────────────────────────────
    "ONLY_USES_MINUTES": {
        "category": "Only Uses Minutes",
        "trigger_keywords": [
            "I only use minutes", "I don't use the internet", "I don't need data",
            "just for calls", "I don't use networks", "only calls",
            "I don't browse", "my cell phone is a flash",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'No need for data'",
                "rebuttal": (
                    "I understand, {{CUSTOMER_NAME}}. But if you're currently only "
                    "recharging by the minute, you're essentially paying every time you "
                    "make a call and not getting any data, social media, or extra benefits "
                    "for your money. With this promotional plan, you not only get unlimited "
                    "minutes, but you also receive high-capacity data that you can share, "
                    "all on a single bill for a similar price to what you're already "
                    "spending. Wouldn't it be better to get more for the same price?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Losing balance' or 'Limited calls'",
                "rebuttal": (
                    "I understand you only use the minutes. But consider this: with prepaid "
                    "plans, your minutes expire. If you don't use them within a few days, "
                    "you lose them! It's like throwing money away. With this postpaid plan, "
                    "you have unlimited minutes to any destination for the entire month, "
                    "without interruptions or worries. Would you like to secure your "
                    "calls once and for all?"
                ),
            },
        ],
    },

    # ── Category 9: Unemployed or Looking for Work ───────────────────────────
    "UNEMPLOYED": {
        "category": "Unemployed or Looking for Work",
        "trigger_keywords": [
            "without a job", "looking for employment", "I have no job", "unemployed",
            "I have no income", "without an office", "looking for a position",
            "difficult situation",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'I can't afford a new expense'",
                "rebuttal": (
                    "I completely understand your situation, {{CUSTOMER_NAME}}. But think "
                    "of it this way: this plan isn't an expense, it's an essential tool "
                    "in today's world. With this high data allowance, you can search for "
                    "jobs with peace of mind, send your resume, participate in video calls, "
                    "and stay connected at all times without relying on Wi-Fi. It's an "
                    "investment in finding your next career path. Would you like to secure "
                    "that connectivity?"
                ),
            },
            {
                "use_when": "Use if user mentions 'I need to save money'",
                "rebuttal": (
                    "Especially when you're looking for a job, missing a call means "
                    "missing an opportunity. With the unlimited minutes included in this "
                    "plan, you're guaranteed to never run out of credit right when you "
                    "get that call for that important interview. Don't let your prepaid "
                    "balance be an obstacle to your next job. Shall we activate this "
                    "benefit so it's always available?"
                ),
            },
        ],
    },

    # ── Category 10: Prepaid Comparison & Ownership ───────────────────────────
    "PREPAID_COMPARISON": {
        "category": "Prepaid Comparison and Ownership",
        "trigger_keywords": [
            "prepaid packages", "monthly surcharge", "package duration",
            "I lost my number", "chip in my name", "recover my line",
            "number security", "validity",
        ],
        "arguments": [
            {
                "use_when": "Use if user says 'My prepaid package lasts the whole month'",
                "rebuttal": (
                    "However, {{CUSTOMER_NAME}}, it's important to clarify that standard "
                    "prepaid packages don't actually last thirty days; they typically last "
                    "for a fraction of a month, depending on your data usage. With "
                    "postpaid, your benefit lasts the entire month without interruption. "
                    "Would you like to secure your connection for the whole month?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Ownership' or 'Fear of losing the number'",
                "rebuttal": (
                    "I understand, but it's crucial to consider that with prepaid plans, "
                    "the line is often not registered in your name. In case of theft, loss, "
                    "or damage to the device, you could permanently lose your number. With "
                    "this postpaid plan, the ownership transfer process is completely free, "
                    "allowing you to recover your line without any problems and protect "
                    "your number forever. It's peace of mind for you. "
                    "Shall we activate this benefit?"
                ),
            },
        ],
    },

    # ── Category 11: Going on a Trip ─────────────────────────────────────────
    "GOING_ON_TRIP": {
        "category": "Going on a Trip",
        "trigger_keywords": [
            "I'm going on a trip", "I'm leaving the city", "vacation", "I won't be around",
            "I'm traveling abroad", "I'm out of town", "out of the country",
        ],
        "arguments": [
            {
                "use_when": "Use if user says 'I won't use it because I'm away'",
                "rebuttal": (
                    "Even while you're traveling, {{CUSTOMER_NAME}}, you won't lose your "
                    "benefits. The promotional discount will remain in place for the first "
                    "few months, so you can enjoy your social media and streaming apps "
                    "from anywhere. Let's activate the plan now to secure all the benefits "
                    "from today and avoid losing the promotion while you're away. "
                    "Does that sound good?"
                ),
            },
            {
                "use_when": "Use if user is traveling abroad or for a long term",
                "rebuttal": (
                    "I understand you're going to travel, that's great! But think carefully: "
                    "your number is the key to your savings account, your online banking, "
                    "and your email. If you leave and leave the prepaid line without topping "
                    "up, the carrier could recycle the number due to inactivity, and you "
                    "could be locked out of your bank accounts while abroad. With this plan, "
                    "you secure your number forever. "
                    "Shall we leave it active for security?"
                ),
            },
        ],
    },

    # ── Category 12: Keypad Phone ─────────────────────────────────────────────
    "KEYPAD_PHONE": {
        "category": "Keypad Phone",
        "trigger_keywords": [
            "keypad phone", "arrow", "old cell phone", "not a smartphone",
            "I don't have apps", "basic cell phone", "I don't have a touch screen",
        ],
        "arguments": [
            {
                "use_when": "Use for a simple technical rebuttal",
                "rebuttal": (
                    "Don't worry, {{CUSTOMER_NAME}}. Even if your phone has a keypad, the "
                    "plan depends on the line, not the device. You can continue using your "
                    "cell phone as usual, with the advantage of a fixed payment and "
                    "unlimited minutes without worrying about recharging. Would you like "
                    "to experience the convenience?"
                ),
            },
            {
                "use_when": "Use if user is focused on price or simplicity",
                "rebuttal": (
                    "Having a keypad phone is actually a huge advantage, because you only "
                    "pay for what you actually use: uninterrupted communication. The "
                    "promotional price I'm offering is so affordable that, for less than "
                    "the cost of a coffee a day, you get unlimited calls and the peace of "
                    "mind of not having to worry about where to recharge. "
                    "Shall we activate this savings?"
                ),
            },
        ],
    },

    # ── Category 13: Bad Coverage ─────────────────────────────────────────────
    "BAD_COVERAGE": {
        "category": "Bad Coverage",
        "trigger_keywords": [
            "bad signal", "calls don't go through", "they drop", "poor coverage",
            "no service", "network down", "Ookla", "I have no signal",
        ],
        "arguments": [
            {
                "use_when": "Use if user is complaining about 'Current issues'",
                "rebuttal": (
                    "I apologize on behalf of Movistar for the recent changes in coverage, "
                    "{{CUSTOMER_NAME}}. We are contacting you precisely because this week, "
                    "over 90% of our customers have access to the service thanks to the "
                    "improvements we've made to our networks. With this plan, you will have "
                    "priority access to all our antennas. Would you like to try the improvement?"
                ),
            },
            {
                "use_when": "Use if user is skeptical or mentions 'Competitors'",
                "rebuttal": (
                    "I understand your concern. But switch with the assurance that an "
                    "external company like Ookla guarantees our current coverage. You'll "
                    "have a stable signal and the fastest speeds in the country. We want "
                    "you to experience the quality of our upgraded network for yourself. "
                    "Shall we activate the benefit?"
                ),
            },
        ],
    },

    # ── Category 14: Line Is for a Minor ─────────────────────────────────────
    # NOTE: Argument 1 was translated from Spanish to English (agent speaks English only).
    "LINE_FOR_MINOR": {
        "category": "Line for a Minor",
        "trigger_keywords": [
            "it's for my son", "it's for a minor", "a girl uses it",
            "it's for my grandson", "my son doesn't need a plan",
            "the child only makes top-ups",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'Safety' or 'Emergency'",
                "rebuttal": (
                    "Precisely because the line is for a minor, {{CUSTOMER_NAME}}, the "
                    "ideal choice is a postpaid plan. Think about it this way: with "
                    "prepaid, if your child runs out of credit in an emergency, they won't "
                    "be able to call you or send you their location on WhatsApp. With this "
                    "plan, you guarantee they're always able to reach you, no matter what "
                    "happens. Doesn't that give you greater peace of mind?"
                ),
            },
            {
                "use_when": "Use if user mentions 'Expense' or 'Usage control'",
                "rebuttal": (
                    "I understand your concern, but I guarantee you'll maintain complete "
                    "control over your spending. The plan has a significant discount with "
                    "a special promotion for the first few months, so you'll end up paying "
                    "less than you currently spend on individual top-ups for your child. "
                    "It's savings and control in one easy decision. "
                    "Shall we get it sorted right away?"
                ),
            },
        ],
    },

    # ── Category 15: Occasional Use ──────────────────────────────────────────
    "OCCASIONAL_USE": {
        "category": "Occasional Use",
        "trigger_keywords": [
            "I don't use it much", "I hardly ever top up", "only for emergencies",
            "I go a long time without using it", "I don't need a plan",
            "I hardly ever call", "I just use Wi-Fi",
        ],
        "arguments": [
            {
                "use_when": "Use if user mentions 'I don't use it enough to justify the cost'",
                "rebuttal": (
                    "Having a postpaid plan is like having insurance for your number, "
                    "{{CUSTOMER_NAME}}. Even if you don't use it much, your line is "
                    "protected, always active, and with the promotional discount I'm giving "
                    "you so you don't have to pay the full price right away. It's ensuring "
                    "your communication for a minimal price. What do you think?"
                ),
            },
            {
                "use_when": "Use if user mentions 'The effort of recharging'",
                "rebuttal": (
                    "Note that with prepaid plans, you have to remember to top up even if "
                    "you don't use it often, to avoid having your line cut off. With "
                    "postpaid plans, you can completely forget about it; your line is "
                    "always active and ready whenever you need it, without any paperwork "
                    "or complications. It's pure convenience for you. "
                    "Shall we activate the benefit?"
                ),
            },
        ],
    },

    # ── Category 16: Closing Tactics & Trust ─────────────────────────────────
    "CLOSING_TRUST": {
        "category": "Closing Tactics and Trust",
        "trigger_keywords": [
            "I don't trust them", "why are they asking for my information",
            "who guarantees this", "it's a scam", "why are they calling me",
            "call security", "SUBTEL",
        ],
        "arguments": [
            {
                "use_when": "Use if user is suspicious or hesitant about the transaction",
                "rebuttal": (
                    "I completely understand. But please note that at no point have I asked "
                    "you to top up your balance or make any kind of money transaction "
                    "through this channel. This call is simply because Movistar wants to "
                    "offer you better communication services. Furthermore, for your "
                    "complete security, this call is being recorded, as we are monitored "
                    "by SUBTEL, and you can request the recording at our branches or "
                    "customer service lines at any time. "
                    "With that reassured, shall we proceed?"
                ),
            },
        ],
    },

    # ── Category 17: Not the Legal Owner ─────────────────────────────────────
    "NOT_LEGAL_OWNER": {
        "category": "Not the Legal Owner",
        "trigger_keywords": [
            "I'm not the account holder", "the line isn't mine",
            "it belongs to my mom", "it belongs to a friend", "I'm not the owner",
            "the line belongs to my boss", "the account holder isn't here",
            "I don't have the papers",
        ],
        "arguments": [
            {
                "use_when": "Official Ownership and Digital Security (Primary Rebuttal)",
                "rebuttal": (
                    "I understand, {{CUSTOMER_NAME}}. However, it's important to know that "
                    "with a prepaid plan, you're not usually the legal owner of the number "
                    "with the regulator. By switching to this postpaid plan, you "
                    "immediately gain official ownership of the line. This protects your "
                    "digital identity, which is directly linked to your bank accounts and "
                    "apps. If your phone is lost or stolen, being the legal owner is the "
                    "only way to ensure you can safely recover your number. Would you like "
                    "to secure ownership of your line today?"
                ),
            },
        ],
    },

    # ── Category 18: Bad Signal or Coverage ───────────────────────────────────
    "BAD_SIGNAL_ROAMING": {
        "category": "Bad Signal or Coverage",
        "trigger_keywords": [
            "bad signal", "call doesn't go through", "it drops", "poor coverage",
            "no service", "network failure", "rural areas", "indoors", "I have no signal",
        ],
        "arguments": [
            {
                "use_when": "Use if user is concerned about 'Signal Availability'",
                "rebuttal": (
                    "If you're worried about signal, please note that our service includes "
                    "a National Roaming protocol, {{CUSTOMER_NAME}}. This means that if "
                    "our main signal is weak in your location, your phone will "
                    "automatically and seamlessly connect to any available partner antenna "
                    "at no extra cost. You're guaranteed to stay connected even in rural "
                    "or indoor areas where other services often fail. "
                    "Would you like that peace of mind?"
                ),
            },
        ],
    },

    # ── Category 19: Fear of Bill Increases ──────────────────────────────────
    "FEAR_OF_BILL_INCREASES": {
        "category": "Fear of Bill Increases",
        "trigger_keywords": [
            "the price is going to go up", "I'm going to be overcharged",
            "expensive bills", "fear of it going up", "extra charges",
            "hidden charges", "surprises on the bill",
        ],
        "arguments": [
            {
                "use_when": "Use if user fears 'Hidden Costs' or 'Price Hikes'",
                "rebuttal": (
                    "I understand your concern, {{CUSTOMER_NAME}}, but this is a "
                    "\"Locked-In Plan.\" This means your monthly fee is 100% fixed and "
                    "locked in; the system technically can't charge you a single penny "
                    "more than the agreed-upon amount. You get the peace of mind of a "
                    "prepaid budget where you know exactly what you're spending, but with "
                    "the superior speed and constant connectivity of a postpaid plan. "
                    "Shall we activate this peace of mind?"
                ),
            },
        ],
    },

    # ── Category 20: Distrust or Fraud Fear ──────────────────────────────────
    "DISTRUST_FRAUD": {
        "category": "Distrust or Fraud Fear",
        "trigger_keywords": [
            "distrust", "fear of fraud", "it's a scam", "who assures me",
            "how do I know it's Movistar", "they're going to rob me",
            "I won't give out my information", "call security",
        ],
        "arguments": [
            {
                "use_when": "Transparency and Official Verification (Primary Rebuttal)",
                "rebuttal": (
                    "It's perfectly valid to be cautious, {{CUSTOMER_NAME}}. For your "
                    "complete security, please note that this process is monitored and "
                    "recorded under strict telecommunications regulations. You can verify "
                    "this offer at any time through our official Mi Movistar app or by "
                    "calling our official customer service line. We provide these "
                    "transparency tools precisely so you can accept this benefit with "
                    "complete peace of mind. Would you like to proceed with the "
                    "brand's security?"
                ),
            },
        ],
    },

    # ── Category 21: Process Hesitation ──────────────────────────────────────
    "PROCESS_HESITATION": {
        "category": "Process Hesitation",
        "trigger_keywords": [
            "I don't know how the process works", "it's very time-consuming",
            "the process scares me", "how do they activate it",
            "what comes next", "doubts about the activation", "paperwork",
        ],
        "arguments": [
            {
                "use_when": "Double Verification and Security (Primary Rebuttal)",
                "rebuttal": (
                    "To ensure everything is perfect, {{CUSTOMER_NAME}}, we have a double "
                    "verification system in place. After we complete the process, a "
                    "dedicated validation team will make a brief follow-up call within "
                    "72 hours just to confirm the details and ensure the benefits are "
                    "activated correctly. This is an extra layer of security for you, "
                    "guaranteeing that what we agreed on today is exactly what you receive. "
                    "Does this backing sound good to you?"
                ),
            },
        ],
    },

    # ── Category 22: $18,500 Recharge Comparison ─────────────────────────────
    "RECHARGE_18500": {
        "category": "18500 Recharge Comparison",
        "trigger_keywords": [
            "I recharge 18500", "eighteen five hundred",
            "the 18 package lasts me the whole month",
            "with 18 thousand I have enough", "18500 prepaid package",
        ],
        "arguments": [
            {
                "use_when": "Use if user claims it lasts 'the whole month'",
                "rebuttal": (
                    "However, it's important to clarify that the $18,500 package doesn't "
                    "actually last thirty days; it typically lasts between fifteen and "
                    "twenty days, depending on usage. Additionally, the data allowance "
                    "isn't unlimited or lifetime, as it comes with a data limit that, once "
                    "used up, causes you to lose the benefit. In contrast, with this "
                    "postpaid plan, you receive up to 99 GB valid for the entire month, "
                    "without having to worry about additional top-ups. "
                    "Ready to upgrade to better browsing?"
                ),
            },
        ],
    },

    # ── Legacy aliases (backward compatibility) ───────────────────────────────
    "NOT_INTERESTED": {
        "category": "Not Interested",
        "trigger_keywords": ["I'm not interested", "I don't want anything"],
        "arguments": [
            {
                "use_when": "Use for a flat 'not interested' with no specific reason given",
                "rebuttal": (
                    "I completely understand. I just want to mention that this is a "
                    "limited-time offer designed specifically for valued customers like you. "
                    "It only takes a minute to hear the details — you might find it's "
                    "exactly the right fit for your needs. Would you be open to a quick overview?"
                ),
            },
        ],
    },
    "HAPPY_WITH_PREPAID": {
        "category": "Happy With Prepaid",
        "trigger_keywords": ["I'm happy with prepaid", "prepaid is fine for me"],
        "arguments": [
            {
                "use_when": "General happiness with prepaid — prefer SATISFIED_WITH_RECHARGES key",
                "rebuttal": (
                    "That's great to hear! Many of our customers felt the same way — until "
                    "they saw how much they were actually spending on top-ups each month. "
                    "With a postpaid plan, you often get significantly more value for the "
                    "same or even less money, plus the peace of mind of never running out "
                    "of balance mid-month. Would you like to hear the details so you can compare?"
                ),
            },
        ],
    },
}
