# Hargassner Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Intégration personnalisée pour les chaudières Hargassner (pellets/biomasse) via l'API cloud Hargassner.

> ⚠️ **Intégration non officielle** — reverse-engineerée depuis l'app Android v1.10.0. Nécessite un compte cloud Hargassner actif.

## Appareils supportés

Testé avec **Nano.2 12**. Devrait fonctionner avec tous les appareils Touch Tronic connectés au cloud.

## Fonctionnalités

| Plateforme | Description |
|---|---|
| `sensor` | Températures chaudière/fumées/départ, stock combustible, température extérieure, état |
| `climate` | Thermostat par circuit de chauffage |
| `number` | Consignes jour/nuit, pente courbe de chauffe, limites désactivation, stock |
| `select` | Mode circuit (Auto/Chauffage/Réduit/Arrêt), chauffage salle de bain |

## Installation via HACS

1. HACS → Intégrations → ⋮ → Dépôts personnalisés
2. Ajouter `https://github.com/VOTRE_USERNAME/hargassner-ha` → **Intégration**
3. Installer "Hargassner" → Redémarrer HA

## Installation manuelle

Copier `custom_components/hargassner/` dans `config/custom_components/` et redémarrer.

## Configuration

Paramètres → Appareils & Services → Ajouter → **Hargassner** → email + mot de passe de l'app mobile.

## Contribuer

Si vous avez un modèle différent et que des entités manquent, ouvrez une issue avec la sortie de :
```bash
curl "https://web.hargassner.at/api/installations/{id}/widgets" -H "Authorization: Bearer {token}" -H "Branding: BRANDING_HARGASSNER"
```

## Disclaimer
Non affilié à Hargassner GmbH.
