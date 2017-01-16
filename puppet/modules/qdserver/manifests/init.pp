class qdserver {
    vcsrepo { '/var/www/qdserver_test':
        ensure   => present,
        provider => git,
        user     => 'apliev',
        source   => 'https://github.com/markflorisson/qdserver.git',
    }
}
