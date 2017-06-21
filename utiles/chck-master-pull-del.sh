#!/bin/sh

# Script que se puede ejecutar luego de haber mergido un PR.
# - Se cambia a la rama principal especificada o master(default)
# - Actualiza la rama principal
# - Elimina la rama que contenía los fixes o fixtures
# - Actualiza el local con las nuevas referencias (fetch -p)
# - Termina mostrando como esta el log actualmente
# EJEMPLO: after-merge fix

DELETE_BRANCH=$1

if [ "$2" ]; then
  MAIN_BRANCH=$2
else
  MAIN_BRANCH=master
fi

echo "ATENCIÓN!\nSe va a eliminar la rama <$DELETE_BRANCH> y se va a actualizar <$MAIN_BRANCH> (Y/n): "
read CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ] || [ "$CONFIRM" = "" ]; then
  git checkout $MAIN_BRANCH
  git pull origin $MAIN_BRANCH
  git branch -D $DELETE_BRANCH
  git fetch -p
  git log --decorate --oneline --all
else
  echo "CANCELADO!"
fi
