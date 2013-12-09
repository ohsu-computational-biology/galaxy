<%inherit file="/base.mako"/>

<%def name="title()">
    ${_('Galaxy History')}
</%def>

<%namespace file="/history/history_panel.mako" import="history_panel_javascripts" />
<%namespace file="/galaxy.masthead.mako" import="get_user_json" />

## -----------------------------------------------------------------------------
<%def name="stylesheets()">
    ${parent.stylesheets()}
    <style>
        body.historyPage {
            margin: 0px;
            padding: 0px;
        }
    </style>
</%def>

## -----------------------------------------------------------------------------
<%def name="javascripts()">
${parent.javascripts()}
${h.js(
    "libs/require",
    "mvc/base-mvc",
    "utils/localization",
    "mvc/user/user-model"
)}
${h.templates( "helpers-common-templates" )}

<script type="text/javascript">
    if( !window.Galaxy ){
        window.Galaxy = {};
        Galaxy.currUser = new User(${h.to_json_string( get_user_json() )});
    }

    $(function(){
        $( 'body' ).addClass( 'historyPage' ).addClass( 'history-panel' );
    });
</script>

${history_panel_javascripts()}

<script type="text/javascript">
function onModuleReady( historyPanel ){
    // attach a panel to selector_to_attach_to and use a history model with bootstrapped data

    // history module is already in the dpn chain from the panel. We can re-scope it here.
    var historyModel    = require( 'mvc/history/history-model' ),
        debugging       = JSON.parse( sessionStorage.getItem( 'debugging' ) ) || false,
        historyJSON     = ${h.to_json_string( history )},
        hdaJSON         = ${h.to_json_string( hdas )};

    var history = new historyModel.History( historyJSON, hdaJSON, {
        logger: ( debugging )?( console ):( null )
    });

    var panel = new historyPanel.HistoryPanel({
        show_deleted    : ${ 'true' if show_deleted == True else ( 'null' if show_deleted == None else 'false' ) },
        show_hidden     : ${ 'true' if show_hidden  == True else ( 'null' if show_hidden  == None else 'false' ) },
        el              : $( "body.historyPage" ),
        model           : history,
        onready         : function(){
            this.render();
            if( Galaxy ){
                Galaxy.currHistoryPanel = this;
            }
        }
    });
}
</script>

</%def>
