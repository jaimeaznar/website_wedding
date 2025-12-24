// app/static/js/translations.js
const translations = {
    en: {
        // Common
        'wedding.title': 'Irene & Jaime\'s Wedding',
        'wedding.date': 'June 6, 2026',
        'our.wedding': 'Our Wedding',

        // Navigation
        'nav.home': 'Home',
        'nav.schedule': 'Schedule',
        'nav.venue': 'Venue',
        'nav.accommodation': 'Accommodation',
        'nav.activities': 'Activities',
        'nav.gallery': 'Gallery',
        'nav.rsvp': 'RSVP',

        // Home page cards
        'card.rsvp': 'RSVP',
        'card.schedule': 'Schedule',
        'card.venue': 'Wedding Venue and Reception',
        'card.accommodation': 'Accommodation',
        'card.activities': 'Activities',
        'card.gallery': 'Gallery',
        'card.countdown': 'Countdown',
        
        // Countdown
        'countdown.days': 'Days',
        'countdown.hours': 'Hours',
        'countdown.minutes': 'Minutes',
        'countdown.seconds': 'Seconds',

        // Footer
        'footer.contact': 'Contact',
        'footer.copyright': '© 2026 aznarroa',

        // RSVP Landing
        'rsvp.title': 'Wedding RSVP',
        'rsvp.landing.message': 'Please use the link provided in your invitation to access the RSVP form.',
        'rsvp.lost.invitation': 'Did you lose your invitation?',
        'rsvp.lost.message': 'If you\'ve lost your invitation with the RSVP link, please contact us directly and we\'ll help you out.',
        'rsvp.return.home': 'Return to Home',

        // RSVP Form
        'rsvp.welcome': 'Welcome',
        'rsvp.last.updated': 'Last updated',
        'rsvp.will.attend': 'Will you attend?',
        'rsvp.yes': 'Yes, I will attend',
        'rsvp.no': 'No, I cannot attend',
        'rsvp.accommodation.title': 'Accommodation',
        'rsvp.where.staying': 'Where are you staying?',
        'rsvp.hotel.placeholder': 'Enter hotel name or leave blank if undecided',
        'rsvp.hotel.help': 'Please let us know where you\'ll be staying.',
        'rsvp.transport.title': 'Transportation',
        'rsvp.transport.question': 'Would you like us to arrange transportation?',
        'rsvp.transport.church': 'Transport to church',
        'rsvp.transport.reception': 'Transport to reception',
        'rsvp.transport.hotel': 'Transport to hotel',
        'rsvp.dietary.title': 'Dietary Restrictions',
        'rsvp.dietary.other': 'Other Dietary Restrictions',
        'rsvp.dietary.placeholder': 'Please specify any other dietary restrictions',
        'rsvp.family.title': 'Family Members',
        'rsvp.additional.adults': 'Number of Additional Adults',
        'rsvp.children.count': 'Number of Children',
        'rsvp.guest.name': 'Name',
        'rsvp.plus.one': 'Plus One',
        'rsvp.submit': 'Submit RSVP',
        'rsvp.cancel': 'Cancel RSVP',
        'rsvp.confirmed': 'You have confirmed your attendance.',
        'rsvp.cancelled': 'RSVP Cancelled',
        'rsvp.cancelled.message': 'Your RSVP has been cancelled.',
        'rsvp.change.mind': 'If you change your mind before the RSVP deadline, please contact us directly at',
        // RSVP Confirmation Pages
        'rsvp.explore.message': 'Now discover all the details about our wedding: venue, hotels, activities, and more!',
        'rsvp.explore.button': 'Explore Wedding Details',
        'rsvp.declined.title': 'Thank You',
        'rsvp.declined.subtitle': 'Thank you for letting us know.',
        'rsvp.declined.sorry': 'We\'re sorry you won\'t be able to join us, but we appreciate you taking the time to respond.',
        'rsvp.declined.change.mind': 'If your plans change before the RSVP deadline, feel free to contact us.',
        'rsvp.cancelled.title': 'RSVP Cancelled',
        'rsvp.cancelled.subtitle': 'Thank you for letting us know.',
        'rsvp.cancelled.sorry': 'We\'re sorry to hear you can no longer attend. We appreciate you informing us.',
        'rsvp.cancelled.change.mind': 'If your situation changes before the RSVP deadline, please contact us directly.',

        // RSVP Confirmations
        'rsvp.thank.you': 'Thank You!',
        'rsvp.excited': 'We\'re excited that you\'ll be joining us for our special day!',
        'rsvp.success': 'Your RSVP has been successfully submitted.',
        'rsvp.update.note': 'You can return to this link at any time before the RSVP deadline to update your response.',
        'rsvp.miss.you': 'We\'ll Miss You',
        'rsvp.declined.message': 'Your RSVP has been recorded as declined.',
        'rsvp.sorry': 'We\'re sorry you can\'t make it to our celebration.',

        // Schedule Modal
        'schedule.title': 'Wedding Schedule',
        'schedule.arrival': 'Guest Arrival & Seating',
        'schedule.arrival.description': 'Please arrive early to be seated before the bride and groom make their entrance.',
        'schedule.ceremony': 'Wedding Ceremony',
        'schedule.ceremony.description': 'Join us as we exchange our vows in the beautiful historic cathedral of Cáceres.',
        'schedule.cathedral': 'Concatedral de Santa María',
        'schedule.travel': 'Travel to Reception',
        'schedule.travel.description': 'Transportation provided',
        'schedule.travel.details': 'Bus transportation will be available for guests traveling from the cathedral to the reception venue.',
        'schedule.reception': 'Reception & Celebration',
        'schedule.reception.description': 'Enjoy an evening of dinner, drinks, and dancing as we celebrate our marriage!',
        'schedule.venue.name': 'Dehesa la Torrecilla, Trujillo',
        'schedule.cocktail': 'Cocktail Hour',
        'schedule.cocktail.description': 'Drinks and appetizers',
        'schedule.dinner': 'Dinner',
        'schedule.dinner.description': 'Traditional Spanish wedding feast',
        'schedule.dancing': 'Dancing & Celebration',
        'schedule.dancing.until': '22:30 - Late',
        'schedule.dancing.description': 'Dance the night away!',
        'schedule.note.title': 'Important:',
        'schedule.note.text': 'Transportation will be provided between the cathedral and reception venue. Please let us know if you need transportation when completing your RSVP.',

        // Venue Modal
        'venue.title': 'Wedding Venue and Reception',
        'venue.location': 'Location',
        'venue.getting.there': 'Getting There',

        // Accommodation Modal
        'accommodation.title': 'Accommodation',
        'accommodation.special.rate': 'Special rate',

        // Accommodation Modal
        'accommodation.intro': 'We\'ve compiled a list of recommended hotels near the ceremony venue. All distances shown are from the Concatedral de Santa María in Cáceres.',
        'accommodation.five.star': 'Luxury Hotels',
        'accommodation.four.star': 'Premium Hotels',
        'accommodation.three.star': 'Comfortable Hotels',
        'accommodation.min': 'min',
        'accommodation.visit': 'Visit Website',
        'accommodation.historic': 'Historic Building',
        'accommodation.boutique': 'Boutique Hotel',
        'accommodation.other.options': 'Other Accommodation Options',
        'accommodation.airbnb.title': 'Airbnb & Vacation Rentals',
        'accommodation.airbnb.text': 'Many beautiful apartments and houses available in Cáceres old town.',
        'accommodation.search': 'Search Airbnb',
        'accommodation.bb.title': 'Bed & Breakfasts',
        'accommodation.bb.text': 'Charming B&Bs throughout the historic center offer authentic local experiences.',
        // Accommodation - Booking.com
        'accommodation.booking.title': 'Search More Hotels on Booking.com',
        'accommodation.booking.text': 'Explore additional hotels and accommodations near the Concatedral de Santa María in Cáceres.',
        'accommodation.booking.note': 'Note: The link is pre-configured for 2 adults, June 5-7, 2026, with hotels near the Concatedral de Santa María. You can adjust the search parameters as needed.',
        'accommodation.booking.search': 'Search on Booking.com',
        // Accommodation - Hotel Descriptions
        'accommodation.hotel.nh.desc': 'Historic palace converted into a luxury hotel in the heart of the old town. Elegant rooms with modern amenities in a 16th-century building.',
        'accommodation.hotel.donmanuel.desc': 'Modern comfort with excellent service. Features a rooftop terrace and contemporary design in a convenient location.',
        'accommodation.hotel.agora.desc': 'Contemporary hotel with comfortable rooms and modern facilities. Great value in a central location.',
        'accommodation.hotel.parador.desc': 'Located in a 14th-century palace within the monumental city. Experience Spanish hospitality in a truly unique setting.',
        'accommodation.hotel.extremadura.desc': 'Modern hotel with spacious rooms and excellent amenities. Perfect for those seeking comfort and convenience.',
        'accommodation.hotel.alcantara.desc': 'Cozy and welcoming hotel offering great value. Clean, comfortable rooms with friendly service.',
        'accommodation.hotel.soho.desc': 'Charming boutique hotel in the old town. Unique rooms with character and personalized service in a prime location.',

        // Accommodation - Additional
        'accommodation.subtitle': 'Where to stay for our special day',
        'accommodation.special.rates.info': 'We\'ve arranged special rates at the following hotels for our wedding guests. Please mention "Irene & Jaime Wedding" when booking to receive the discounted rate.',
        'accommodation.book.now': 'Book Now',
        'accommodation.alternatives.intro': 'There are also several alternative accommodations in the area:',
        'accommodation.map.title': 'Accommodation Map',
        'accommodation.map.placeholder': 'Map will be embedded here',

        // Accommodation - Hotel Descriptions
        'accommodation.hotel.nh.desc': 'Palacio histórico convertido en hotel de lujo en el corazón del casco antiguo. Habitaciones elegantes con comodidades modernas en un edificio del siglo XVI.',
        'accommodation.hotel.donmanuel.desc': 'Confort moderno con excelente servicio. Cuenta con terraza en la azotea y diseño contemporáneo en una ubicación conveniente.',
        'accommodation.hotel.agora.desc': 'Hotel contemporáneo con habitaciones cómodas e instalaciones modernas. Excelente relación calidad-precio en una ubicación céntrica.',
        'accommodation.hotel.parador.desc': 'Ubicado en un palacio del siglo XIV dentro de la ciudad monumental. Experimenta la hospitalidad española en un entorno verdaderamente único.',
        'accommodation.hotel.extremadura.desc': 'Hotel moderno con habitaciones amplias y excelentes comodidades. Perfecto para quienes buscan confort y comodidad.',
        'accommodation.hotel.alcantara.desc': 'Hotel acogedor que ofrece una excelente relación calidad-precio. Habitaciones limpias y cómodas con servicio amable.',
        'accommodation.hotel.soho.desc': 'Encantador hotel boutique en el casco antiguo. Habitaciones únicas con carácter y servicio personalizado en una ubicación privilegiada.',
        
        // Activities Modal
        'activities.title': 'Things to Do',
        'activities.location': 'Location',
        'activities.cost': 'Cost',
        // Activities - Days
        'activities.friday': 'Friday - Cáceres Old Town',
        'activities.saturday': 'Saturday Morning - Cáceres Exploration',
        'activities.sunday': 'Sunday - Trujillo Day Trip',
        'activities.tips': 'Helpful Tips',
        // Activities Modal - Introduction & Sections
        'activities.intro': 'Explore the beautiful medieval towns of Cáceres and Trujillo while you\'re here for our wedding!',
        'activities.friday.desc': 'Arrive and explore the UNESCO World Heritage medieval city.',
        'activities.saturday.desc': 'Explore more before the wedding celebration.',
        'activities.sunday.desc': 'Discover the hometown of conquistadors (45 minutes from Cáceres).',

        // Activities - Friday
        'activities.plaza.mayor': 'Plaza Mayor & Old Town',
        'activities.plaza.mayor.desc': 'Start your visit at the historic Plaza Mayor and enter the walled city through the stunning Arco de la Estrella.',
        'activities.torre.bujaco': 'Torre de Bujaco',
        'activities.torre.bujaco.desc': 'Climb this 12th-century tower for panoramic views of the city and surrounding countryside.',
        'activities.tapas.tour': 'Evening Tapas Tour',
        'activities.tapas.tour.desc': 'Sample local Extremadura specialties: Torta del Casar cheese, Iberian ham, and migas cacereñas.',

        // Activities - Saturday
        'activities.palaces.walk': 'Medieval Palaces Walk',
        'activities.palaces.walk.desc': 'Discover the noble palaces, historic facades, and medieval architecture of the old quarter.',
        'activities.shopping': 'Historic Shopping Streets',
        'activities.shopping.desc': 'Browse local shops for crafts, souvenirs, and regional products in charming medieval lanes.',
        'activities.cathedral.visit': 'Co-Cathedral Visit',
        'activities.cathedral.visit.desc': 'Explore the stunning Gothic Cathedral and peaceful surrounding alleys before the wedding.',

        // Activities - Sunday (Trujillo)
        'activities.trujillo.plaza': 'Plaza Mayor de Trujillo',
        'activities.trujillo.plaza.desc': 'Visit the stunning main square featuring the iconic statue of Francisco Pizarro and historic buildings.',
        'activities.trujillo.castle': 'Castillo de Trujillo',
        'activities.trujillo.castle.desc': 'Climb to the medieval castle for breathtaking views of the town and surrounding countryside.',
        'activities.trujillo.lunch': 'Old Town Lunch & Stroll',
        'activities.trujillo.lunch.desc': 'Enjoy traditional Extremadura cuisine on a terrace and wander the charming cobbled streets.',

        // Activities - Labels
        'activities.time': 'Time',
        'activities.evening': 'Evening',
        'activities.variable': 'Variable',

        // Activities - Tips
        'activities.tip.footwear': 'Wear comfortable shoes - many streets are cobbled!',
        'activities.tip.timing': 'Trujillo is 45 minutes from Cáceres by car',
        'activities.tip.parking': 'Check parking near your accommodation in advance',
        'activities.tip.weather': 'Bring layers - evenings can be cool',
        'activities.tip.dining': 'Make reservations for Saturday dinner',
        'activities.tip.language': 'Basic Spanish phrases are helpful in smaller towns',
        'activities.tip.footwear.label': 'Footwear:',
        'activities.tip.timing.label': 'Timing:',
        'activities.tip.parking.label': 'Parking:',
        'activities.tip.weather.label': 'Weather:',
        'activities.tip.dining.label': 'Dining:',
        'activities.tip.language.label': 'Language:',

        // Dress Code Card
        'card.dresscode': 'Dress Code',

        // Dress Code Modal
        'dresscode.title': 'Dress Code',
        'dresscode.intro': 'Our wedding is an evening celebration. Please dress accordingly.',
        'dresscode.women.title': 'Women',
        'dresscode.women.recommended': 'Long evening dresses',
        'dresscode.please.avoid': 'Please avoid:',
        'dresscode.women.no.white': 'White or beige colors',
        'dresscode.women.no.patterns': 'Patterns',
        'dresscode.women.no.sequins': 'Sequins',
        'dresscode.men.title': 'Men',
        'dresscode.men.recommended': 'Dark suit',
        'dresscode.thanks': 'Thank you for helping us make this evening elegant and memorable!',


        // Gallery Modal
        'gallery.title': 'Our Gallery',
        'gallery.first.meet': 'First time we met',
        'gallery.engagement': 'Our engagement day',
        'gallery.traveling': 'Traveling together',
        'gallery.special': 'Special moments',
        'gallery.holiday': 'Holiday memories',
        'gallery.celebrating': 'Celebrating together',

        // Common actions
        'action.close': 'Close',
        'action.submit': 'Submit',
        'action.cancel': 'Cancel',
        'action.back': 'Go Back',
        'action.confirm': 'Confirm',

        // Alerts and messages
        'alert.changes.restricted': 'Changes Restricted',
        'alert.changes.not.possible': 'Changes are not possible within',
        'alert.days.of.wedding': 'days of the wedding date.',
        'alert.need.assistance': 'Need assistance? Contact us at:',
        'alert.deadline.passed': 'RSVP Deadline Has Passed',
        'alert.deadline.message': 'We\'re sorry, but the RSVP deadline has passed.',
        'alert.current.status': 'Your Current RSVP Status:',
        'alert.confirmed.attendance': 'You have confirmed your attendance. Thank you!',
        'alert.declined.invitation': 'You have declined the invitation.',
        'alert.make.changes': 'If you need to make changes to your RSVP, please contact us directly.',

        // Additional texts
        'child': 'Child',
        'adult': 'Additional Adult',
        'none': 'None',
        'free': 'Free',
        'per.person': 'per person',
        'for.tasting': 'for tasting tour',

        // Gifts Card
        'card.gifts': 'Gifts',
        
        // Gifts Modal
        'gifts.title': 'Wedding Gifts',
        'gifts.intro': 'Your presence at our wedding is the greatest gift of all! However, if you wish to give a gift, a contribution toward our future together would be greatly appreciated.',
        'gifts.bank.title': 'Bank Transfer',
        'gifts.bank.name': 'Account Name:',
        'gifts.copied': 'IBAN copied to clipboard!',
        'gifts.thanks': 'Thank you for your generosity and for being part of our special day!',

        'confirmation_explore': "Now explore everything about the wedding!",
        'declined_explore': "Feel free to explore the wedding details in case your plans change:",
        'back_home': "Back to Home",

        // Allergens
        'allergen.gluten': 'Gluten',
        'allergen.dairy': 'Dairy',
        'allergen.nuts': 'Nuts (Tree nuts)',
        'allergen.peanuts': 'Peanuts',
        'allergen.soy': 'Soy',
        'allergen.eggs': 'Eggs',
        'allergen.fish': 'Fish',
        'allergen.shellfish': 'Shellfish',
        'allergen.celery': 'Celery',
        'allergen.mustard': 'Mustard',
        'allergen.sesame': 'Sesame',
        'allergen.sulphites': 'Sulphites',
        'allergen.lupins': 'Lupins',
        'allergen.molluscs': 'Molluscs',
        'allergen.vegetarian': 'Vegetarian',
        'allergen.vegan': 'Vegan',
        'allergen.kosher': 'Kosher',
        'allergen.halal': 'Halal',
    },
    es: {
        // Common
        'wedding.title': 'Boda de Irene y Jaime',
        'wedding.date': '6 de Junio, 2026',
        'our.wedding': 'Nuestra Boda',

        // Navigation
        'nav.home': 'Inicio',
        'nav.schedule': 'Programa',
        'nav.venue': 'Lugar',
        'nav.accommodation': 'Alojamiento',
        'nav.activities': 'Actividades',
        'nav.gallery': 'Galería',
        'nav.rsvp': 'RSVP',

        // Home page cards
        'card.rsvp': 'Confirmación',
        'card.schedule': 'Programa',
        'card.venue': 'Ceremonia y banquete',
        'card.accommodation': 'Alojamiento',
        'card.activities': 'Actividades',
        'card.gallery': 'Galería',
        'card.countdown': 'Cuenta Atrás',
        
        // Countdown
        'countdown.days': 'Días',
        'countdown.hours': 'Horas',
        'countdown.minutes': 'Minutos',
        'countdown.seconds': 'Segundos',

        // Footer
        'footer.contact': 'Contacto',
        'footer.copyright': '© 2026 aznarroa',

        // RSVP Landing
        'rsvp.title': 'Confirmación de Boda',
        'rsvp.landing.message': 'Por favor, usa el enlace proporcionado en tu invitación para acceder al formulario de confirmación.',
        'rsvp.lost.invitation': '¿Has perdido tu invitación?',
        'rsvp.lost.message': 'Si has perdido tu invitación con el enlace de confirmación, por favor contáctanos directamente y te ayudaremos.',
        'rsvp.return.home': 'Volver al Inicio',

        // RSVP Form
        'rsvp.welcome': 'Bienvenido/a',
        'rsvp.last.updated': 'Última actualización',
        'rsvp.will.attend': '¿Asistirás?',
        'rsvp.yes': 'Sí, asistiré',
        'rsvp.no': 'No, no puedo asistir',
        'rsvp.accommodation.title': 'Alojamiento',
        'rsvp.where.staying': '¿Dónde te alojarás?',
        'rsvp.hotel.placeholder': 'Introduce el nombre del hotel o déjalo en blanco si no lo has decidido',
        'rsvp.hotel.help': 'Por favor, haznos saber dónde te alojarás.',
        'rsvp.transport.title': 'Transporte',
        'rsvp.transport.question': '¿Te gustaría que organicemos el transporte?',
        'rsvp.transport.church': 'Transporte a la iglesia',
        'rsvp.transport.reception': 'Transporte a la recepción',
        'rsvp.transport.hotel': 'Transporte al hotel',
        'rsvp.dietary.title': 'Restricciones Dietéticas',
        'rsvp.dietary.other': 'Otras Restricciones Dietéticas',
        'rsvp.dietary.placeholder': 'Por favor especifica cualquier otra restricción dietética',
        'rsvp.family.title': 'Miembros de la Familia',
        'rsvp.additional.adults': 'Número de Adultos Adicionales',
        'rsvp.children.count': 'Número de Niños',
        'rsvp.guest.name': 'Nombre',
        'rsvp.plus.one': 'Acompañante',
        'rsvp.submit': 'Enviar confirmación',
        'rsvp.cancel': 'Cancelar confirmación',
        'rsvp.confirmed': 'Has confirmado tu asistencia.',
        'rsvp.cancelled': 'Confirmación Cancelada',
        'rsvp.cancelled.message': 'Tu confirmación ha sido cancelado.',
        'rsvp.change.mind': 'Si cambias de opinión antes de la fecha límite de la confimación, por favor contáctanos directamente en',
        // RSVP Confirmation Pages  
        'rsvp.explore.message': '¡Descubre todos los detalles de nuestra boda: lugar, hoteles, actividades y más!',
        'rsvp.explore.button': 'Explorar Detalles de la Boda',
        'rsvp.declined.title': 'Gracias',
        'rsvp.declined.subtitle': 'Gracias por hacérnoslo saber.',
        'rsvp.declined.sorry': 'Sentimos que no puedas acompañarnos, pero agradecemos que te hayas tomado el tiempo de responder.',
        'rsvp.declined.change.mind': 'Si tus planes cambian antes de la fecha límite, no dudes en contactarnos.',
        'rsvp.cancelled.title': 'Confirmación Cancelada',
        'rsvp.cancelled.subtitle': 'Gracias por informarnos.',
        'rsvp.cancelled.sorry': 'Lamentamos saber que ya no puedes asistir. Agradecemos que nos lo hayas comunicado.',
        'rsvp.cancelled.change.mind': 'Si tu situación cambia antes de la fecha límite, por favor contáctanos directamente.',

        // RSVP Confirmations
        'rsvp.thank.you': '¡Gracias!',
        'rsvp.excited': '¡Estamos emocionados de que nos acompañes en nuestro día especial!',
        'rsvp.success': 'Tu confirmación se ha enviado correctamente.',
        'rsvp.update.note': 'Puedes volver a este enlace en cualquier momento antes de la fecha límite de la confirmación para actualizar tu respuesta.',
        'rsvp.miss.you': 'Te Echaremos de Menos',
        'rsvp.declined.message': 'Tu confirmación ha sido registrada como rechazada.',
        'rsvp.sorry': 'Sentimos que no puedas asistir a nuestra celebración.',

        // Schedule Modal
        'schedule.title': 'Programa de la Boda',
        'schedule.arrival': 'Llegada y Asientos de Invitados',
        'schedule.arrival.description': 'Por favor, llega temprano para estar sentado antes de la entrada de los novios.',
        'schedule.ceremony': 'Ceremonia de Boda',
        'schedule.ceremony.description': 'Acompáñanos mientras intercambiamos nuestros votos en la hermosa catedral histórica de Cáceres.',
        'schedule.cathedral': 'Concatedral de Santa María',
        'schedule.travel': 'Viaje a la Recepción',
        'schedule.travel.description': 'Transporte proporcionado',
        'schedule.travel.details': 'Habrá transporte en autobús disponible para los invitados que viajen desde la catedral hasta el lugar de la recepción.',
        'schedule.reception': 'Recepción y Celebración',
        'schedule.reception.description': '¡Disfruta de una velada de cena, bebidas y baile mientras celebramos nuestro matrimonio!',
        'schedule.venue.name': 'Dehesa la Torrecilla, Trujillo',
        'schedule.cocktail': 'Hora de Cóctel',
        'schedule.cocktail.description': 'Bebidas y aperitivos',
        'schedule.dinner': 'Cena',
        'schedule.dinner.description': 'Banquete tradicional español de boda',
        'schedule.dancing': 'Baile y Celebración',
        'schedule.dancing.description': '¡Baila toda la noche!',
        'schedule.dancing.until': '22:30 - Cierre',
        'schedule.note.title': 'Importante:',
        'schedule.note.text': 'Se proporcionará transporte entre la catedral y el lugar de la recepción. Por favor, haznos saber si necesitas transporte al completar tu confirmación.',

        // Venue Modal
        'venue.title': 'Ceremonia y banquete',
        'venue.location': 'Ubicación',
        'venue.getting.there': 'Cómo Llegar',

        // Accommodation Modal
        'accommodation.title': 'Alojamiento',
        'accommodation.special.rate': 'Tarifa especial',

        // Accommodation Modal
        'accommodation.intro': 'Hemos recopilado una lista de hoteles recomendados cerca del lugar de la ceremonia. Todas las distancias mostradas son desde la Concatedral de Santa María en Cáceres.',
        'accommodation.five.star': 'Hoteles de Lujo',
        'accommodation.four.star': 'Hoteles Premium',
        'accommodation.three.star': 'Hoteles Confortables',
        'accommodation.min': 'min',
        'accommodation.visit': 'Visitar Sitio Web',
        'accommodation.historic': 'Edificio Histórico',
        'accommodation.boutique': 'Hotel Boutique',
        'accommodation.other.options': 'Otras Opciones de Alojamiento',
        'accommodation.airbnb.title': 'Airbnb y Alquileres Vacacionales',
        'accommodation.airbnb.text': 'Muchos apartamentos y casas hermosas disponibles en el casco antiguo de Cáceres.',
        'accommodation.search': 'Buscar en Airbnb',
        'accommodation.bb.title': 'Casas Rurales y B&B',
        'accommodation.bb.text': 'Encantadoras casas rurales en el centro histórico ofrecen experiencias locales auténticas.',
        // Accommodation - Booking.com
        'accommodation.booking.title': 'Buscar Más Hoteles en Booking.com',
        'accommodation.booking.text': 'Explora hoteles adicionales y alojamientos cerca de la Concatedral de Santa María en Cáceres.',
        'accommodation.booking.note': 'Nota: El enlace está preconfigurado para 2 adultos, 5-7 de junio de 2026, con hoteles cerca de la Concatedral de Santa María. Puedes ajustar los parámetros de búsqueda según sea necesario.',
        'accommodation.booking.search': 'Buscar en Booking.com',

        // Activities Modal
        'activities.title': 'Qué Hacer',
        'activities.location': 'Ubicación',
        'activities.cost': 'Coste',
        // Current in your file:
        'activities.friday': 'Viernes - Casco Antiguo de Cáceres',
        'activities.saturday': 'Sábado por la Mañana - Explorando Cáceres',
        'activities.sunday': 'Domingo - Excursión a Trujillo',
        'activities.tips': 'Consejos Útiles',
        // Activities Modal - Introduction & Sections
        'activities.intro': '¡Explora las hermosas ciudades medievales de Cáceres y Trujillo mientras estás aquí para nuestra boda!',
        'activities.friday.desc': 'Llega y explora la ciudad medieval Patrimonio de la Humanidad de la UNESCO.',
        'activities.saturday.desc': 'Explora más antes de la celebración de la boda.',
        'activities.sunday.desc': 'Descubre la ciudad natal de los conquistadores (45 minutos desde Cáceres).',

        // Activities - Friday
        'activities.plaza.mayor': 'Plaza Mayor y Casco Antiguo',
        'activities.plaza.mayor.desc': 'Comienza tu visita en la histórica Plaza Mayor y entra en la ciudad amurallada a través del impresionante Arco de la Estrella.',
        'activities.torre.bujaco': 'Torre de Bujaco',
        'activities.torre.bujaco.desc': 'Sube a esta torre del siglo XII para disfrutar de vistas panorámicas de la ciudad y el campo circundante.',
        'activities.tapas.tour': 'Ruta de Tapas por la Noche',
        'activities.tapas.tour.desc': 'Prueba las especialidades locales de Extremadura: Torta del Casar, jamón ibérico y migas cacereñas.',

        // Activities - Saturday
        'activities.palaces.walk': 'Paseo por los Palacios Medievales',
        'activities.palaces.walk.desc': 'Descubre los palacios nobles, las fachadas históricas y la arquitectura medieval del casco antiguo.',
        'activities.shopping': 'Calles Comerciales Históricas',
        'activities.shopping.desc': 'Explora las tiendas locales de artesanía, recuerdos y productos regionales en encantadoras calles medievales.',
        'activities.cathedral.visit': 'Visita a la Concatedral',
        'activities.cathedral.visit.desc': 'Explora la impresionante Catedral Gótica y los tranquilos callejones que la rodean antes de la boda.',

        // Activities - Sunday (Trujillo)
        'activities.trujillo.plaza': 'Plaza Mayor de Trujillo',
        'activities.trujillo.plaza.desc': 'Visita la impresionante plaza principal con la icónica estatua de Francisco Pizarro y edificios históricos.',
        'activities.trujillo.castle': 'Castillo de Trujillo',
        'activities.trujillo.castle.desc': 'Sube al castillo medieval para disfrutar de vistas impresionantes del pueblo y el campo circundante.',
        'activities.trujillo.lunch': 'Almuerzo y Paseo por el Casco Antiguo',
        'activities.trujillo.lunch.desc': 'Disfruta de la cocina tradicional extremeña en una terraza y pasea por las encantadoras calles empedradas.',

        // Activities - Labels
        'activities.time': 'Tiempo',
        'activities.evening': 'Noche',
        'activities.variable': 'Variable',

        // Activities - Tips
        'activities.tip.footwear': '¡Usa zapatos cómodos - muchas calles son empedradas!',
        'activities.tip.timing': 'Trujillo está a 45 minutos de Cáceres en coche',
        'activities.tip.parking': 'Consulta el aparcamiento cerca de tu alojamiento con antelación',
        'activities.tip.weather': 'Lleva capas de ropa - las noches pueden ser frescas',
        'activities.tip.dining': 'Haz reservas para la cena del sábado',
        'activities.tip.language': 'Frases básicas en español son útiles en pueblos pequeños',
        'activities.tip.footwear.label': 'Calzado:',
        'activities.tip.timing.label': 'Tiempo:',
        'activities.tip.parking.label': 'Aparcamiento:',
        'activities.tip.weather.label': 'Clima:',
        'activities.tip.dining.label': 'Cenas:',
        'activities.tip.language.label': 'Idioma:',

        // Accommodation - Additional
        'accommodation.subtitle': 'Dónde alojarse para nuestro día especial',
        'accommodation.special.rates.info': 'Hemos acordado tarifas especiales en los siguientes hoteles para nuestros invitados. Por favor, menciona "Boda de Irene y Jaime" al reservar para obtener el descuento.',
        'accommodation.book.now': 'Reservar Ahora',
        'accommodation.alternatives.intro': 'También hay varias opciones de alojamiento alternativas en la zona:',
        'accommodation.map.title': 'Mapa de Alojamientos',
        'accommodation.map.placeholder': 'El mapa se mostrará aquí',

        // Dress Code Card
        'card.dresscode': 'Código de Vestimenta',

        // Dress Code Modal
        'dresscode.title': 'Código de Vestimenta',
        'dresscode.intro': 'Nuestra boda es una celebración de tarde. Por favor, vestid de acuerdo a la ocasión.',
        'dresscode.women.title': 'Mujeres',
        'dresscode.women.recommended': 'Vestido largo de tarde',
        'dresscode.please.avoid': 'Por favor, evitad:',
        'dresscode.women.no.white': 'Colores blanco o beige',
        'dresscode.women.no.patterns': 'Estampados',
        'dresscode.women.no.sequins': 'Lentejuelas',
        'dresscode.men.title': 'Hombres',
        'dresscode.men.recommended': 'Traje oscuro',
        'dresscode.thanks': '¡Gracias por ayudarnos a hacer esta velada elegante y memorable!',

        // Gallery Modal
        'gallery.title': 'Nuestra Galería',
        'gallery.first.meet': 'Primera vez que nos conocimos',
        'gallery.engagement': 'Nuestro día de compromiso',
        'gallery.traveling': 'Viajando juntos',
        'gallery.special': 'Momentos especiales',
        'gallery.holiday': 'Recuerdos de vacaciones',
        'gallery.celebrating': 'Celebrando juntos',

        // Common actions
        'action.close': 'Cerrar',
        'action.submit': 'Enviar',
        'action.cancel': 'Cancelar',
        'action.back': 'Volver',
        'action.confirm': 'Confirmar',

        // Alerts and messages
        'alert.changes.restricted': 'Cambios Restringidos',
        'alert.changes.not.possible': 'No es posible hacer cambios dentro de',
        'alert.days.of.wedding': 'días de la fecha de la boda.',
        'alert.need.assistance': '¿Necesitas ayuda? Contáctanos en:',
        'alert.deadline.passed': 'La Fecha Límite de la confirmación ha pasado',
        'alert.deadline.message': 'Lo sentimos, pero la fecha límite de la confirmación ha pasado.',
        'alert.current.status': 'Tu Estado de confirmación actual:',
        'alert.confirmed.attendance': 'Has confirmado tu asistencia. ¡Gracias!',
        'alert.declined.invitation': 'Has rechazado la invitación.',
        'alert.make.changes': 'Si necesitas hacer cambios en tu confirmación, por favor contáctanos directamente.',

        // Additional texts
        'child': 'Niño',
        'adult': 'Adulto Adicional',
        'none': 'Ninguno',
        'free': 'Gratis',
        'per.person': 'por persona',
        'for.tasting': 'para tour de cata',

        // Gifts Card
        'card.gifts': 'Regalos',
        
        // Gifts Modal
        'gifts.title': 'Regalos de Boda',
        'gifts.intro': '¡Vuestra presencia en nuestra boda es el mayor regalo! Sin embargo, si deseáis hacer un regalo, una contribución para nuestro futuro juntos sería muy apreciada.',
        'gifts.bank.title': 'Transferencia Bancaria',
        'gifts.bank.name': 'Nombre de Cuenta:',
        'gifts.copied': '¡IBAN copiado al portapapeles!',
        'gifts.thanks': '¡Gracias por vuestra generosidad y por ser parte de nuestro día especial!',
        'confirmation_explore': "¡Ahora explora todo sobre la boda!",
        'declined_explore': "Si cambias de opinión, aquí tienes toda la información:",
        'back_home': "Volver al inicio",

        // Allergens
        'allergen.gluten': 'Gluten',
        'allergen.dairy': 'Lácteos',
        'allergen.nuts': 'Frutos secos',
        'allergen.peanuts': 'Cacahuetes',
        'allergen.soy': 'Soja',
        'allergen.eggs': 'Huevos',
        'allergen.fish': 'Pescado',
        'allergen.shellfish': 'Mariscos',
        'allergen.celery': 'Apio',
        'allergen.mustard': 'Mostaza',
        'allergen.sesame': 'Sésamo',
        'allergen.sulphites': 'Sulfitos',
        'allergen.lupins': 'Altramuces',
        'allergen.molluscs': 'Moluscos',
        'allergen.vegetarian': 'Vegetariano',
        'allergen.vegan': 'Vegano',
        'allergen.kosher': 'Kosher',
        'allergen.halal': 'Halal',
    }
};

// Translation system
class TranslationSystem {
    constructor() {
        this.currentLang = localStorage.getItem('preferredLanguage') || 'es';
        this.translations = translations;
    }

    setLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('preferredLanguage', lang);
        document.documentElement.lang = lang;
        this.updatePageTranslations();
        this.updateLanguageButtons();
    }

    t(key) {
        return this.translations[this.currentLang][key] || this.translations['en'][key] || key;
    }

    updatePageTranslations() {
        // Update all elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = this.t(key);

            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.placeholder) {
                    element.placeholder = translation;
                }
            } else {
                element.textContent = translation;
            }
        });

        // Update all elements with data-translate-placeholder attribute
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            const translation = this.t(key);
            element.placeholder = translation;
        });

        // Handle allergen labels with fallback
        document.querySelectorAll('[data-allergen-fallback]').forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = this.translations[this.currentLang][key];
            if (translation) {
                element.textContent = translation;
            } else {
                // Use fallback if no translation found
                element.textContent = element.getAttribute('data-allergen-fallback');
            }
        });
    }

    updateLanguageButtons() {
        // Update language button states using data-lang attribute
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === this.currentLang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    // Helper method to translate dynamic content
    translateDynamic(key, replacements = {}) {
        let translation = this.t(key);
        Object.keys(replacements).forEach(placeholder => {
            translation = translation.replace(`{${placeholder}}`, replacements[placeholder]);
        });
        return translation;
    }
}

// Initialize translation system when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    window.translator = new TranslationSystem();

    // Set initial language and update buttons
    window.translator.updatePageTranslations();
    window.translator.updateLanguageButtons();

    // Handle language button clicks
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('lang-btn')) {
            e.preventDefault();
            const newLang = e.target.getAttribute('data-lang');
            window.translator.setLanguage(newLang);
        }
    });
});

// Export for use in other scripts
window.TranslationSystem = TranslationSystem;