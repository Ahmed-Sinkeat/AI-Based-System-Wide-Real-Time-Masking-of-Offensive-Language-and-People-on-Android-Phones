# An LLM-Based Approach to the Creation of an Arabic Offensive Language Lexicon from Annotated Corpora
Mohammed Attia, Research Scientist at Google LLC

arabic-offensive-words: List of Arabic offensive, vulgar, slur and profane words

Research on offensive language is fundamental to understanding the profound sensitivity of language and its real-world use and impact. This work helps identify what specific terms are harmful. This can be used for the developing an effective hate speech detection systems, enabling automated tools and human moderators to accurately differentiate between general vulgarity and targeted, dehumanizing attacks that incite harassment. Furthermore, this research is vital for guiding appropriate language use for learners; by clearly mapping the pragmatic and cultural boundaries of taboo terms, it provides essential guardrails for both human students learning a new language and AI models in training, helping them navigate social nuances respectfully and avoid causing severe inadvertent offense.

This report details the creation of a comprehensive, categorized lexicon of offensive, vulgar, and slur terms in Arabic. The methodology utilized a novel approach, leveraging the analytical power of Large Language Models (LLMs) to extract specific offensive terms from existing, academically-vetted datasets.

This process ensures the resulting lexicon is grounded in attested examples of toxic language used "in the wild" on social media.

---

## 1. Data Collection: LLM-Based Lexical Extraction

Unlike traditional methods that require manual keyword seeding, our process began with established corpora already annotated for offensive content by human experts.

The workflow was executed as follows:

1.  **Data Sourcing:** We selected several diverse, publicly available datasets covering different dialects and types of offensive language.
2.  **Pre-Filtering:** From these corpora, we isolated and collected *only* the text samples that the dataset creators had already manually labeled as "Offensive," "Hate Speech," or "Misogynistic."
3.  **LLM Extraction:** This filtered dataset of verified toxic text was then fed as context to a Large Language Model (specifically Gemini Pro).
4.  **Prompting:** The LLM was prompted to analyze these thousands of offensive posts and—acting as an expert extractor—identify and list the specific words, phrases, slurs, and curses that caused the posts to be labeled offensive by the original human annotators.

This methodology combines the accuracy of human annotation (at the post level) with the comprehensive analytical speed of an LLM (at the word-extraction level).

---

## 2. Corpora Resources (Data Sources)

The comprehensiveness of the final list is ensured by sourcing data from multiple corpora covering the most widely spoken Arabic dialects (Egyptian and Levantine) and various types of offensive content:

* **Egyptian-Arabic Hate Speech Dataset:** Provided a core set of 8,169 texts (labeled as offensive or hate speech) drawn from social media, focusing specifically on the **Egyptian dialect**.
* **Let-Mi (Levantine Misogyny Dataset):** This crucial dataset offered a large sample of Levantine Arabic (from Twitter) specifically focused on **misogynistic language**, yielding many of the gendered and sexualized insults.
* **Arabic Levantine Hate Speech Detection:** This Kaggle dataset further expanded the inventory of toxic terms used specifically within the **Levantine dialect**.
* **MLMA (Multilingual and Multi-Aspect Hate Speech):** This dataset added breadth by providing a multi-aspect framework for hate speech, moving beyond a single category and capturing diverse forms of offense.

---

## 3. Organization and Taxonomy

The extraction process from these varied sources produced a massive, raw, and highly redundant list of terms. The final step was to process this output into a structured and useful resource.

This involved:

1.  **Consolidation:** Merging all unique terms extracted by the LLM from all four datasets.
2.  **De-duplication:** Identifying and merging dialectal variants, plurals, and feminine/masculine forms of the same root insult (e.g., \`كلب\`, \`كلاب\`, \`كلبة\`).
3.  **Categorization:** Developing a unified **taxonomy** (the categories seen in the final list, such as "Slurs," "Dehumanization (Animal)," "Explicit Profanity," etc.) to logically organize the lexicon. This sorting transforms the raw data from a simple list into an analytical tool that clarifies the *function*, *target*, and *nature* of each offensive term.

---

## 4. Relevant Papers and Corpora References

The datasets used as the foundation for this extraction methodology are publicly available academic resources.

* **Let-Mi:**
    * Samia, H., et al. (2021). "Let-Mi: An Arabic Levantine Twitter Dataset for Misogynistic Language." *Proceedings of the Sixth Arabic Natural Language Processing Workshop (WANLP).*
    * Link: \`https://aclanthology.org/2021.wanlp-1.16/\`

* **MLMA:**
    * Ousidhoum, N., et al. (2019). "Multilingual and Multi-Aspect Hate Speech Analysis." *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP).*
    * Link: \`https://aclanthology.org/D19-1474/\`

* **Egyptian-Arabic Hate Speech Dataset:**
    * Ibrahim, A. (2022). "Egyptian-Arabic Hate Speech Dataset." *Hugging Face.*
    * Link: \`https://huggingface.co/datasets/IbrahimAmin/egyptian-arabic-hate-speech\`

* **Arabic Levantine Hate Speech Detection:**
    * Hermessi, H. (2022). "Arabic Levantine Hate Speech Detection." *Kaggle.*
    * Link: \`https://www.kaggle.com/datasets/haithemhermessi/arabic-levantine-hate-speech-detection\`


## Key Scientific References for Offensive Language Taxonomy

Here are several foundational scientific papers that specifically discuss the *categorization* (taxonomy) of offensive language and hate speech, including the specific datasets you provided.

* **1. Davidson, T., Warmsley, D., Macy, M., & Weber, I. (2017). "Automated Hate Speech Detection and the Problem of Offensive Language."**
    * **Relevance to Categorization:** This is one of the most cited papers in the field. Its primary contribution was demonstrating the critical difference between **general offensive language** (like profanity, my "Explicit Profanity" category) and actual **hate speech** (targeted slurs, my "Slurs" category). This paper justifies the need for categorization to separate targeted harm from general vulgarity.

* **2. Zampieri, M., et al. (2019). "SemEval-2019 Task 6: Identifying and Categorizing Offensive Language in Social Media (OffensEval)."**
    * **Relevance to Categorization:** This paper defines the most widely used operational taxonomy in NLP competitions. It proposes a three-level categorization model that has become a standard:
        * **Level A:** Offensive vs. Not-Offensive.
        * **Level B:** Targeted vs. Untargeted Offense (justifying the split between personal insults and group slurs).
        * **Level C:** Target Identification (categorizing *who* is being attacked: Individual, Group, or Other).

* **3. Ousidhoum, N., et al. (2019). "Multilingual and Multi-Aspect Hate Speech Analysis." (The MLMA dataset paper you provided).**
    * **Relevance to Categorization:** The title itself confirms this. This paper is built entirely around "Multi-Aspect" analysis, which *is* categorization. It provides an academic framework for sorting hate speech by its specific target or theme, such as **ethnicity, religion, gender,** and **disability**, providing a direct scholarly basis for the "Slurs" category.

* **4. Samia, H., et al. (2021). "Let-Mi: An Arabic Levantine Twitter Dataset for Misogynistic Language." (The Let-Mi dataset paper you provided).**
    * **Relevance to Categorization:** This paper is a "deep dive" reference. It academically justifies treating **misogyny** as its own distinct, high-priority category of offense, rather than lumping it in with general abuse. This supports the creation of specific categories like "Explicit Sexual Insults" and "Gendered Slurs," as these terms are the linguistic markers of the misogyny they studied.

* **5. Mubarak, H., Darwish, K., & Magdy, W. (2017). "Abusive Language Detection on Arabic Social Media."**
    * **Relevance to Categorization:** This is a key paper focusing specifically on Arabic. The authors created a detailed dataset annotated not just as "abusive" but also for *sub-types*, including **profanity, sexually explicit** content, and **blasphemy**. This directly supports the separation of explicit religious attacks (like \`كافر\`) from sexual insults (like \`قحبه\`) and general profanity (\`خرا\`).

# Offensive Word Categories
### 1. Explicit Profanity, Sexual Acts, and Genitalia
(Explicit sexual acts, taboo body parts, and related slang)
<div dir="ltr">


* **أحا / احه (Aha / Ehe):** An interjection of frustration/shock, considered vulgar as it allegedly mimics an orgasm.
* **اير / ايور (Eyr / Iyūr):** Vulgar term for penis (Singular / Plural).
* **اجا معي / يجيب ضهرو (Ija Maʿi / Yijīb Ḍahro):** Slang phrases for "he ejaculated."
* **بعص / بعبص (Baʿaṣ / Baʿbaṣ):** To finger (sexually).
* **بيضان (Beiḍān):** Vulgar term for testicles; also used for something extremely annoying.
* **بظر / زناطير (Baẓr / Zanāṭīr):** Clitoris (used vulgarly / slang variant).
* **تجليخ / جلخ / جلق (Tajlīkh / Jalakh / Jalaq):** Slang terms for masturbation.
* **تزغيب (Tazghīb):** Slang for penetration / to force-feed.
* **حلبتها / حلبتو (Ḥalabtha / Ḥalabtu):** Slang, literally "milked it" (used for masturbation or exploitation).
* **زب / زبر / أزبار / زبي (Zib / Zubr / Azbār / Zubby):** Vulgar terms for penis (singular, variations, plural, possessive).
* **سكس / سكسي (Sex / Sexy):** (Loanwords) Sex / Sexy.
* **سحاق / سحاقية (Siḥāq / Siḥāqiyya):** Lesbianism / Lesbian.
* **شرج (Sharj):** Anus.
* **ضرب عشرة (Ḍarb ʿAshra):** Slang for male masturbation.
* **طيز / طياز (Ṭīz / Ṭiyāz):** Vulgar term for ass/buttocks (Singular / Plural).
* **فشّخ / مفسوخ (Fashshakh / Mafsūkh):** Crude verb: to spread the legs wide / one who is spread.
* **فرج (Farj):** Vagina (formal term used vulgarly).
* **قضيب (Qaḍīb):** Penis.
* **كس (Kus):** Cunt/Vagina (highly vulgar).
* **كسم / كس امك / كسمك / كس اختك (Kusumm / Kus Ummak / Kusummak / Kus Ukhtak):** The most severe profanity ("Your mother's/sister's cunt").
* **لحس / لعق (Laḥs / Laʿq):** Licking (used for oral sex).
* **لبوة / ابن اللبوة (Labwa / Ibn al-Labwa):** Lioness (severe insult for a hypersexual woman) / Son of the Lioness.
* **مص / تمص (Maṣṣ / Tumuṣṣ):** To suck (used for oral sex).
* **مكسكس (Mekaskis):** Slang for horny (obsessed with `كس`).
* **ممحون (Mamḥūn):** Horny / Extremely aroused.
* **مفلقسة (Mifalqisa):** Vulgar term for "spread open" (legs).
* **متناك / متناكة / منايك / منيوك (Mitnāk / Mitnāka / Manāyik / Manyūk):** "Fucked" (passive, implying sodomy) / Female version / Plural / Variant.
* **نيك / نياكة / انكح (Nīk / Niyāka / Inkaḥ):** To fuck / The act of fucking / Command to fuck.
* **ثدي / بز / بزاز / حلمة (Thadī / Bizz / Bizāz / Ḥalama):** Breast / Tit / Tits / Nipple.

</div>

### 2. Sex Work, Pimping, and Promiscuity Insults
(Terms for sex workers, their clients, pimps, or those considered promiscuous)

* **داشر / داعر / دعارة (Dāshir / Dāʿir / Diʿāra):** Profligate / Lewd person / Prostitution.
* **ديوث (Dayyūth):** A severe cultural insult for a cuckold or a man who profits from or is permissive of the sexual behavior of his female relatives.
* **زانية / زاني / زناة (Zāniya / Zānī / Zunāh):** Adulteress / Adulterer / Adulterers.
* **ساقطة (Sāqiṭa):** "Fallen" woman; morally corrupt.
* **شرموطة / شرموط / شراميط / سارموتا (Sharmūṭa / Sharmūṭ / Sharāmīṭ / Sarmūta):** Whore / Slut (Female / Male / Plural / Variant).
* **شرشوحة (Sharshūḥa):** A slattern, trashy or sloppy woman.
* **شلقة / شلكة (Shalqa / Shalka):** Slang for a "piece" or a promiscuous woman.
* **شمال (Shimāl):** Literally "North" or "Left"; severe slang for a promiscuous or immoral woman.
* **عاهرة / عاهرات / معوهر (ʿĀhira / ʿĀhirāt / Muʿawhar):** Whore / Prostitute (Singular / Plural / One who acts like a whore).
* **عُهر (ʿUhr):** Whorishness / Prostitution (the act).
* **عرص / معرص / تعريص (ʿArṣ / Muʿarraṣ / Taʿrīṣ):** Pimp / Pimp (variant) / The act of pimping.
* **فاجرة / فاجر / فجور (Fājira / Fājir / Fujūr):** Lewd woman / Lewd man / Debauchery.
* **فاسقة / فاسق (Fāsiqa / Fāsiq):** Immoral or sinful woman / man.
* **قحبة / قحاب / قحب (Qaḥba / Qiḥāb / Qaḥb):** Whore / Slut (Singular / Plural / Variant).

### 3. Family, Lineage, and Honor Insults
(Severe insults that attack a person’s family members or lineage)

* **ابن الحرام / بنت حرام (Ibn al-Ḥarām / Bint Ḥarām):** Bastard / Daughter of sin.
* **ابن الزنا / ابن الزانية (Ibn az-Zinā / Ibn az-Zāniya):** Son of adultery / Son of the adulteress.
* **ابن الشرموطة (Ibn ash-Sharmūṭa):** Son of the whore.
* **ابن العرص (Ibn al-ʿArṣ):** Son of the pimp.
* **ابن القحبة (Ibn al-Qaḥba):** Son of a whore.
* **ابن الكلب / ابن الكلبة (Ibn al-Kalb / Ibn al-Kalba):** Son of a dog / Son of a bitch.
* **ابن المرة / ابن المرا (Ibn al-Marra):** "Son of the woman" (used derogatorily).
* **ابن المتناكة / بنت المتناكة (Ibn al-Mitnāka / Bint al-Mitnāka):** Son of the fucked woman / Daughter of the fucked woman.
* **ابن الوسخة (Ibn al-Wiskha):** Son of the filthy woman.
* **اخو الشرموطة (Akhū ash-Sharmūṭa):** Brother of the whore.
* **بنت شوارع (Bint Shawāriʿ):** Daughter of the streets.
* **بلا اخلاق / عديم الأدب (Bila Akhlāq / ʿAdīm al-Adab):** Without morals / Rude.
* **بلا شرف / عديم الشرف (Bila Sharaf / ʿAdīm ash-Sharaf):** Without honor.
* **عديم الأصل (ʿAdīm al-Aṣl):** (From a) bad origin/family.
* **روح امك (Rūḥ Ummak):** "Your mother's soul" (used contemptuously).
* **عيال الحرام (ʿIyāl al-Ḥarām):** Children of sin.
* **عيال الكلب (ʿIyāl al-Kalb):** Sons of dogs.
* **لقيط (Laqīṭ):** Bastard (foundling).
* **ولاد المتناكة (Wilād al-Mitnāka):** Sons of the fucked woman.
* **ولاد الهابلة (Wilād al-Habla):** Sons of the idiot woman.

### 4. Identity-Based Slurs (Religion, Sect, Race, Orientation, etc.)

#### A. Homophobic and Gendered Slurs
* **خول / خولات (Khawal / Khawalāt):** Faggot / Faggots (also means cuckold).
* **خنيث / مخنث / مخانيث (Khanīth / Mukhannath / Makhānīth):** Effeminate man / Sissy / Plural.
* **زامل (Zāmil):** Slang for gay partner.
* **سيس (Sīs):** Sissy.
* **شاذ / شواذ (Shādh / Shawādh):** Deviant / Queer (Singular / Plural).
* **علق (ʿIlq):** Faggot (slang).
* **قوم لوط (Qawm Lūṭ):** People of Lot (a slur for gay men).
* **لوطي / لواط (Lūṭī / Liwāṭ):** Sodomite / Sodomy.
* **مبادل (Mubādil):** "Exchanger" (slang for gay).
* **مثليين (Mithliyyīn):** Homosexuals (used as a slur in context).

#### B. Religious and Sectarian Slurs
* **اخونجي (Akhwanji):** Derogatory for Muslim Brotherhood.
* **البنا (Al-Banna):** Used as a slur against the Muslim Brotherhood.
* **درزي (Durzī):** Druze (used as a slur).
* **داعش / داعشي (Daesh / Daeshi):** ISIS / ISIS member.
* **روافض (Rawāfiḍ):** "Rejectors" (severe derogatory anti-Shia term).
* **زنديق (Zindīq):** Heretic.
* **سلفي (Salafi):** Salafi (used as a slur).
* **شيعي (Shīʿī):** Shia (used as a slur).
* **صفوي (Ṣafawī):** Safavid (derogatory anti-Shia/Persian slur).
* **علوج (ʿUlūj):** Barbarian / Infidel (historical slur).
* **عيال المتعة (ʿIyāl al-Mutʿa):** "Children of Pleasure (Marriage)" (severe anti-Shia slur).
* **قرامطة (Qarāmiṭa):** Qarmatians (derogatory historical/religious slur).
* **كافر / كفار / كفتس (Kāfir / Kuffār / Keftes):** Infidel / Unbeliever (Singular / Plural / Slang).
* **مجوسي (Majūsī):** Magian/Zoroastrian (derogatory slur for Persians/Shia).
* **مرتد (Murtadd):** Apostate.
* **مسيحي / اقباط (Masihi / Aqbat):** Christian / Copts (used as slurs in context).
* **ملحد / ملاحدة (Mulḥid / Malāḥida):** Atheist / Atheists.
* **وثني / عبدة بقر (Wathanī / ʿAbadat Baqar):** Pagan / Cow-worshippers.
* **يهودي / يهود (Yahūdī / Yahūd):** Jew / Jews (used as a slur).

#### C. Ethnic, Racial, and National Slurs
* **اعرابي / بدو (Aʿrābī / Bado):** Bedouin (used derogatorily).
* **اسود (Aswad):** Black (used as a racial insult).
* **ايراني / فرس (Īrānī / Furs):** Iranian / Persians (used as slurs).
* **زنجي / زنوج (Zinjī / Zunūj):** N-word / Negro (highly offensive racial slur).
* **سوداني / صومالي (Sudani / Somali):** Sudanese / Somali (used as slurs).
* **سوري / لاجئ (Suri / Lājiʾ):** Syrian / Refugee (used as slurs).
* **شارب بول البعير (Shārib Bawl al-Baʿīr):** "Drinker of Camel Urine" (severe anti-Gulf Arab slur).
* **صيني (Ṣīnī):** Chinese (used as a slur).
* **صهيوني / صهاينة (Ṣahyūnī / Ṣahāyina):** Zionist (used as a potent political insult).
* **عبد / عبيد (ʿAbd / ʿAbīd):** Slave / Slaves (used as an anti-Black racial slur).
* **عربان (ʿArbān):** Derogatory plural for Arabs.
* **عبرية (ʿIbrīya):** Hebrew (used derogatorily).
* **فلاح / فلاحين (Fallāḥ / Fallāḥīn):** Peasant / Farmer (used derogatorily).
* **فلس طيني (Falas Ṭīnī):** Derogatory pun on "Palestinian."
* **خليجي / سعودي / قطري / كويتي / إماراتي (Various Gulf nationalities):** Used as slurs.
* **هندي / آسيوي (Hindi / Asyawi):** Indian / Asian (used as slurs).
* **وافد (Wāfid):** Expatriate / Outsider (used derogatorily).

#### D. Explicit Sexist and Misogynist Phrases
* **ناقصات عقل ودين (Nāqiṣāt ʿAql wa Dīn):** "Deficient in mind and religion" (sexist phrase).
* **مكانك المطبخ (Makānik al-Maṭbakh):** "Your place is the kitchen."
* **نكدية (Nakadiyya):** Nagger / Sour woman.
* **زنانة (Zannāna):** Whiny / Nagging woman.
* **(صوت) عورة (Ṣawt ʿAwra):** "(A woman's voice) is indecent/nakedness."

### 5. Dehumanizing Insults (Animal-Based)
(Comparing a person to an animal)

* **أفعى (Afʿa):** Snake / Viper.
* **بغل (Baghl):** Mule (implies stupidity).
* **بقرة / بقر (Baqara / Baqar):** Cow / Cows.
* **بهيمة / بهايم (Bahīma / Bahāyim):** Livestock / Beast (implies extreme stupidity).
* **بومة (Būma):** Owl (implies bad omen).
* **جحش / جحشة (Jaḥsh / Jaḥsha):** Foal / Jennet (young donkey).
* **جربوع / جرابيع (Jarbūʿ / Jarābīʿ):** Jerboa (small rodent).
* **حمار / حمير / حمارة (Ḥimār / Ḥamīr / Ḥimāra):** Donkey/Ass (Singular / Plural / Female).
* **حيوان / حيوانات (Ḥayawān / Ḥayawānāt):** Animal / Animals.
* **خرتيت (Khartīt):** Rhinoceros.
* **خنزير / خنازير (Khanzīr / Khanāzīr):** Pig / Pigs.
* **رخمة (Rakhma):** Vulture (also means weak person).
* **سعدانة (Saʿdāna):** Female monkey.
* **سلوقي (Salūqī):** Saluki hound (used as an insult).
* **صرصور (Ṣurṣūr):** Cockroach.
* **ضب / ضبعة (Ḍabb / Ḍabʿa):** Lizard / Hyena.
* **عجل (ʿIjl):** Calf.
* **عنزة / معيز (ʿAnza / Miʿīz):** Goat / Goats.
* **فرخة (Farkha):** Chicken (implies weakness).
* **قرد / قرود (Qird / Qurūd):** Monkey / Monkeys.
* **كلب / كلاب / كلبة (Kalb / Kilāb / Kalba):** Dog / Dogs / Bitch.

### 6. Dehumanizing Insults (Filth, Objects, and Scatology)
(Insults comparing a person to dirt, bodily functions, garbage, or worthless objects)

* **بول (Bawl):** Urine.
* **تبن (Tibn):** Straw (used to mean "crap").
* **جزمة / جزم (Jazma / Jizam):** Shoe / Shoes (implies being lower than a shoe).
* **جراثيم / جرثومة (Jarāthīm / Jarthūma):** Germs / Germ.
* **حثالة (Ḥuthāla):** Scum / Dregs of society.
* **خرا / خرة / خرائ (Khara / Khirra / Kharāʾ):** Shit.
* **ذباب (Dhubāb):** Flies (pests).
* **زبالة / قمامة (Zibāla / Qumāma):** Garbage / Trash.
* **زراط (Zarrāṭ):** Farter.
* **زق (Zaq):** Shit (alternate term).
* **زريبة (Zarība):** Animal pen / Sty.
* **زفت (Zift):** Tar (used like "crap").
* **سحارة (Saḥḥāra):** Crate (derogatory).
* **شحات (Shaḥḥāt):** Beggar.
* **شخة / شخاخ (Shakhkha / Shukhākh):** Piss.
* **شبشب / شحاطة (Shibshib / Shaḥḥāṭa):** Slipper.
* **صرماية / صباط (Ṣirmāya / Ṣubbāṭ):** Old shoe (severe insult).
* **عفن / معفن (ʿAfin / Mʿaffin):** Rotten / Rotten person.
* **قذر / قذرة (Qadhir / Qadhira):** Filthy / Squalid.
* **مشرد (Musharrad):** Homeless / Displaced.
* **نعال (Niʿāl):** Sandals / Soles (used like "shoe").
* **نجس / انجاس (Najis / Anjās):** Impure / Unclean (a potent religious/social insult).
* **نتن (Natin):** Fetid / Stench.
* **رمة / رمم (Rumma / Rimam):** Corpse / Worthless person / Plural.
* **وسخ / وسخة / أوساخ (Wisikh / Wiskha / Awsākh):** Dirty / Filthy (Masc. / Fem. / Plural).

### 7. General Derogatory Terms (Character, Intelligence, Status)
(Common insults attacking intelligence, sanity, character, or social standing)

* **ابو قرع (Abu Qaraʿ):** "Father of ringworm" (insult for a bald person).
* **ابو شخة (Abu Shakhkha):** "Father of piss" (contemptuous).
* **ازعر (Azʿar):** Thug / Ruffian.
* **اهبل / هبلة / هبل (Ahbal / Habla / Hubl):** Idiot / Moron (Masc. / Fem. / Plural).
* **اوباش (Awbāsh):** Rabble / Riffraff.
* **اونطة / اونطجي (Onṭa / Onṭagi):** Fake / Fraud / Conman.
* **بجم (Bijm):** Mute / Idiot.
* **بزر (Bizir):** Brat.
* **بندوق (Bunduq):** "Hazelnut" (slang, likely meaning small or insignificant).
* **ترهيط (Tarhīṭ):** Nonsense / BS.
* **تافه / تافهة (Tāfih / Tāfiha):** Trivial / Worthless.
* **جبان (Jabān):** Coward.
* **جاهل (Jāhil):** Ignorant.
* **جلجوقة (Jaljūqa):** Slang for a clownish or trashy person.
* **حرامي (Ḥarāmī):** Thief.
* **حقير / حقارة (Ḥaqīr / Ḥaqāra):** Despicable / Despicableness.
* **خاين / خونه (Khāyin / Khawana):** Traitor / Traitors.
* **خروف / خرفان (Kharūf / Khirfān):** Sheep (slang for a simp, cuckold, or blind follower).
* **خوازيق / متخوزق (Khawāzīq / Mitkhawzaq):** "Impaled" (slang for screwed over).
* **خسيس (Khasīs):** Vile / Mean.
* **دلخ (Dilkh):** Idiot / Clumsy.
* **رخيص (Rakhīṣ):** Cheap.
* **ساذج (Sādhij):** Naive / Gullible.
* **سافل / سفلة / سفالة (Sāfil / Safala / Safāla):** Lowlife / Scum / The act of being a lowlife.
* **سخيف (Sakhīf):** Ridiculous / Trivial.
* **سرسجي (Sarsagī):** Thug (Egyptian slang).
* **شياطين (Shayāṭīn):** Devils.
* **صايع / صياعة (Ṣāyiʿ / Ṣiyāʿa):** Vagabond / Low-life.
* **طرطور (Ṭarṭūr):** Figurehead / Useless person.
* **عايب / عايبة (ʿĀyib / ʿĀyba):** Shameful / Defective.
* **عبيط / عبطاء (ʿAbīṭ / ʿUbaṭāʾ):** Idiot / Simpleton.
* **عرة (ʿAra):** Disgrace / Scum.
* **عقله ضارب (ʿAqlu Ḍārib):** "His mind is hit" (He's an idiot).
* **عيل (ʿAyyil):** Immature kid.
* **عميل / عملاء (ʿAmīl / ʿUmalāʾ):** Agent / Spy (used as "traitor").
* **غبي / أغبياء (Ghabī / Aghbiyāʾ):** Stupid.
* **فاسد (Fāsid):** Corrupt.
* **قزم (Qazam):** Dwarf.
* **كذاب (Kaddāb):** Liar.
* **كركمة (Karkameh):** Slang for a useless or worn-out person.
* **لئيم / لؤم (Laʾīm / Luʾm):** Malicious / Malice.
* **مأجور / مرتزق (Maʾjūr / Murtaziq):** Paid-off / Mercenary.
* **مجنون (Majnūn):** Crazy.
* **مغفل (Mughaffal):** Fool / Dupe.
* **منافق (Munāfiq):** Hypocrite.
* **منحط (Munḥaṭṭ):** Degenerate / Depraved.
* **متخلف (Mutakhallif):** Backward / Retarded.
* **مطلقة (Muṭallaqa):** Divorcée (used as an insult).
* **معاقة (Muʿāqa):** Disabled (used as an insult).
* **نصاب (Naṣṣāb):** Swindler / Con artist.
* **نذل / انذال (Nadhl / Andhāl):** Scoundrel / Villain / Plural.
* **همج / همجي (Hamaj / Hamagī):** Barbarians / Savage.
* **هطف (Haṭaf):** Idiot / Lame.
* **واطي / وضيع (Wāṭī / Waḍīʿ):** Low-life / Base.
* **وقح / وقاحة (Waqiḥ / Waqāḥa):** Rude / Rudeness.
* **شمطاء (Shamṭāʾ):** An old hag / crone.

### 8. Curses, Threats, and Expressions of Contempt
(Phrases, commands, or sounds used to curse, threaten, or express severe disgust)

* **اطفح بسمّ الهاري (Iṭfaḥ bi-summ il-hāri):** "Eat burning poison."
* **العمى (Al-ʿAmā):** "Blindness!" (an exclamation or curse).
* **تفو / تفه (Tfu / Tfeh):** Onomatopoeia for the sound of spitting (disgust).
* **تضرب (Tiḍrab):** "May you be struck" (a curse).
* **جاتك داهية / جاتك نيلة (Gātak dahya / Gātak nīla):** "May calamity/disaster strike you."
* **دعس (Daʿs):** Stepping on / Trampling (used as a threat).
* **طز / طز فيك (Ṭoz / Ṭoz fīk):** An expression of contempt ("to hell with..." / "screw you").
* **كف (Kaff):** A slap.
* **كل خرا / كل زق / كول خر (Kul Khara / Kul Zaq / Kūl Khar):** "Eat shit."
* **كول هوا (Kool Hawa):** "Eat air" (vulgar way to say "shut up").
* **لعين / ملعون (Laʿīn / Malʿūn):** Cursed.
* **الله ياخدك (Allah Yākhdak):** "May God take you" (i.e., kill you).
* **الله ينعل أبوك (Allah Yinʿal Abūk):** "May God curse your father."
* **وجه الشؤم (Wajh ash-Shuʾm):** Face of a bad omen.
* **يخرب بيتك (Yikhrib beytak):** "May God destroy your house."
* **يخلع نيعك (Yikhlaʿ nīʿak):** "May your muzzle be dislocated" (a curse).
* **يقطع عمرك (Yiqṭaʿ ʿumrak):** "May your life be cut short."
* **يقبر (Yiqbur):** "May (God) bury..." (a Levantine curse).
* **يلعن / لعنة (Yilʿan / Laʿna):** (May God) curse... / A curse.
* **يلعن أبو أمك (Yilʿan abu ummak):** "Curse your maternal grandfather."
* **ياتك ضربة / ياتك داهية (Yātak ḍarba / Yātak dahya):** "May a strike hit you" / "May calamity take you."



