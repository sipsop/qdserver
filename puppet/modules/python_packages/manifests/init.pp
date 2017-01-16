class python_packages {

    class { 'python' :
        version    => 'python3',
        pip        => 'present',
        dev        => 'present',
    }

    package { 'build-essential':
        require => Class['python'],
        ensure => installed,
    }

    python::pip { 'flask' :
        pkgname => 'flask',
        ensure  => 'latest',
    ;
    'pyyaml' :
        pkgname => 'pyyaml',
        ensure  => 'latest',
    ;
    'gevent' :
        pkgname => 'gevent',
        ensure  => 'latest',
    ;
    'rethinkdb' :
        pkgname => 'rethinkdb',
        ensure  => 'latest',
    ;
    'dateutils' :
        pkgname => 'dateutils',
        ensure  => 'latest',
    ;
    'Flask-Sockets' :
        pkgname => 'Flask-Sockets',
        ensure  => 'latest',
    ;
    'Flask-uWSGI-WebSocket' :
        pkgname => 'Flask-uWSGI-WebSocket',
        ensure  => 'latest',
    ;
    'websocket-client' :
        pkgname => 'websocket-client',
        ensure  => 'latest',
    ;
    'wsaccel' :
        pkgname => 'wsaccel',
        ensure  => 'latest',
    ;
    'ujson' :
        pkgname => 'ujson',
        ensure  => 'latest',
    ;
    'colorama' :
        pkgname => 'colorama',
        ensure  => 'latest',
    ;
    'pytest' :
        pkgname => 'pytest',
        ensure  => 'latest',
    ;
    'pytest-quickcheck' :
        pkgname => 'pytest-quickcheck',
        ensure  => 'latest',
    ;
    'gipc' :
        pkgname => 'gipc',
        ensure  => 'latest',
    ;
    'jwt' :
        pkgname => 'jwt',
        ensure  => 'latest',
    }

}
