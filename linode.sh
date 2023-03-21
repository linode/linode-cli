# This is a generated file by Linode-CLI! Do not modify!
_linode_cli()
{
local cur prev opts
COMPREPLY=()
cur="${COMP_WORDS[COMP_CWORD]}"
prev="${COMP_WORDS[COMP_CWORD-1]}"

case "${prev}" in
    linode-cli)
        COMPREPLY=( $(compgen -W "account events payment-methods service-transfers users databases domains images linodes kernels stackscripts lke longview managed networking firewalls vlans nodebalancers object-storage profile security-questions sshkeys phone regions tickets tags volumes --help" -- ${cur}) )
        return 0
        ;;
    account)
        COMPREPLY=( $(compgen -W "view update cancel invoices-list invoice-view invoice-items logins-list login-view maintenance-list notifications-list clients-list client-create client-view client-update client-delete client-reset-secret payments-list payment-create payment-view promo-add settings settings-update enable-managed transfer --help" -- ${cur}) )
        return 0
        ;;
        events)
        COMPREPLY=( $(compgen -W "list view mark-read mark-seen --help" -- ${cur}) )
        return 0
        ;;
        payment-methods)
        COMPREPLY=( $(compgen -W "list add view delete default --help" -- ${cur}) )
        return 0
        ;;
        service-transfers)
        COMPREPLY=( $(compgen -W "list create view cancel accept --help" -- ${cur}) )
        return 0
        ;;
        users)
        COMPREPLY=( $(compgen -W "list create view update delete --help" -- ${cur}) )
        return 0
        ;;
        databases)
        COMPREPLY=( $(compgen -W "engines engine-view list mongodb-list mongodb-view mongodb-update mongodb-delete mongodb-backups-list mongodb-backup-snapshot mongodb-backup-view mongodb-backup-delete mongodb-backup-restore mongodb-creds-view mongodb-creds-reset mongodb-ssl-cert mongodb-patch mysql-list mysql-create mysql-view mysql-update mysql-delete mysql-backups-list mysql-backup-snapshot mysql-backup-view mysql-backup-delete mysql-backup-restore mysql-creds-view mysql-creds-reset mysql-ssl-cert mysql-patch postgresql-list postgresql-create postgresql-view postgresql-update postgresql-delete postgresql-backups-list postgresql-backup-snapshot postgresql-backup-view postgresql-backup-delete postgresql-backup-restore postgresql-creds-view postgresql-creds-reset postgresql-ssl-cert postgresql-patch types type-view --help" -- ${cur}) )
        return 0
        ;;
        domains)
        COMPREPLY=( $(compgen -W "list create view update delete zone-file import clone records-list records-create records-view records-update records-delete --help" -- ${cur}) )
        return 0
        ;;
        images)
        COMPREPLY=( $(compgen -W "list create upload view update delete --help" -- ${cur}) )
        return 0
        ;;
        linodes)
        COMPREPLY=( $(compgen -W "list create view update delete backups-list snapshot backups-cancel backups-enable backup-view backup-restore boot clone configs-list config-create config-view config-update config-delete disks-list disk-create disk-view disk-update disk-delete disk-clone disk-reset-password disk-resize firewalls-list ips-list ip-add ip-view ip-update ip-delete migrate upgrade nodebalancers linode-reset-password reboot rebuild rescue resize shutdown transfer-view volumes types type-view --help" -- ${cur}) )
        return 0
        ;;
        kernels)
        COMPREPLY=( $(compgen -W "list view --help" -- ${cur}) )
        return 0
        ;;
        stackscripts)
        COMPREPLY=( $(compgen -W "list create view update delete --help" -- ${cur}) )
        return 0
        ;;
        lke)
        COMPREPLY=( $(compgen -W "clusters-list cluster-create cluster-view cluster-update cluster-delete pools-list pool-create cluster-nodes-recycle pool-view pool-update pool-delete pool-recycle node-view node-delete node-recycle api-endpoints-list cluster-dashboard-url kubeconfig-view kubeconfig-delete regenerate service-token-delete versions-list version-view --help" -- ${cur}) )
        return 0
        ;;
        longview)
        COMPREPLY=( $(compgen -W "list create view update delete plan-view plan-update subscriptions-list subscription-view --help" -- ${cur}) )
        return 0
        ;;
        managed)
        COMPREPLY=( $(compgen -W "contacts-list contact-create contact-view contact-update contact-delete credentials-list credential-create credential-view credential-update credential-update-username-password credential-revoke credential-sshkey-view issues-list issue-view linode-settings-list linode-setting-view linode-setting-update services-list service-create service-view service-update service-delete service-disable service-enable stats-list --help" -- ${cur}) )
        return 0
        ;;
        networking)
        COMPREPLY=( $(compgen -W "ips-list ip-add ip-view ip-update ip-assign ip-share v6-pools v6-ranges v6-range-create v6-range-view v6-range-delete --help" -- ${cur}) )
        return 0
        ;;
        firewalls)
        COMPREPLY=( $(compgen -W "list create view update delete devices-list device-create device-view device-delete rules-list rules-update --help" -- ${cur}) )
        return 0
        ;;
        vlans)
        COMPREPLY=( $(compgen -W "list --help" -- ${cur}) )
        return 0
        ;;
        nodebalancers)
        COMPREPLY=( $(compgen -W "list create view update delete configs-list config-create config-view config-update config-delete config-rebuild nodes-list node-create node-view node-update node-delete --help" -- ${cur}) )
        return 0
        ;;
        object-storage)
        COMPREPLY=( $(compgen -W "clusters-list clusters-view keys-list keys-create keys-view keys-update keys-delete cancel ssl-view ssl-upload ssl-delete --help" -- ${cur}) )
        return 0
        ;;
        profile)
        COMPREPLY=( $(compgen -W "view update apps-list app-view app-delete tfa-disable tfa-enable tfa-confirm tokens-list token-create token-view token-update token-delete logins-list login-view devices-list device-view device-revoke --help" -- ${cur}) )
        return 0
        ;;
        security-questions)
        COMPREPLY=( $(compgen -W "list --help" -- ${cur}) )
        return 0
        ;;
        sshkeys)
        COMPREPLY=( $(compgen -W "list create view update delete --help" -- ${cur}) )
        return 0
        ;;
        phone)
        COMPREPLY=( $(compgen -W "sms-code-send delete verify --help" -- ${cur}) )
        return 0
        ;;
        regions)
        COMPREPLY=( $(compgen -W "list view --help" -- ${cur}) )
        return 0
        ;;
        tickets)
        COMPREPLY=( $(compgen -W "list create view close replies reply --help" -- ${cur}) )
        return 0
        ;;
        tags)
        COMPREPLY=( $(compgen -W "list create delete --help" -- ${cur}) )
        return 0
        ;;
        volumes)
        COMPREPLY=( $(compgen -W "list create view update delete attach clone detach resize --help" -- ${cur}) )
        return 0
        ;;
    *)
        ;;
esac
}

complete -F _linode_cli linode-cli
complete -F _linode_cli linode
complete -F _linode_cli lin
