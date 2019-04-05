<?
include('db.php');

class User {
  public static function me() {
    return $_SESSION['id'] ?? false;
  }

  public static function create($data) {
    $data['password'] = password_hash($data['password']);
    return db_insert('users', $data);
  }

  public static function update($user = false, $data = []) {
    $user = $user ?? self::me();
    return db_update($user, $data);
  }

  public static function login($email, $pass) {
    if(! ($user = Get::user(['email' => $email]) ) {
      throw new Exception("User $email not found");
    }
    if( password_hash($pass) != $user['password'] ) {
      throw new Exception("User $email password incorrect");
    }
    $_SESSION['id'] = $user['id'];
    return true;
  }

  public static function logout() {
    session_destroy();
  }
};
