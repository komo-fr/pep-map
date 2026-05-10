var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

/**
 * GroupBadges - グループIDの配列をバッジとして表示するカスタムセルレンダラー
 *
 * props.value: グループIDの配列 (例: [1, 5, 12])
 * props.setData: クリック時にDashにデータを送信する関数
 * props.data: 行データ全体（cited_by_groups_detail, cites_groups_detailを含む）
 * props.colDef.field: カラムのフィールド名（"cited_by_groups" or "cites_groups"）
 * props.groupInfo: グループ情報のマッピング {groupId: {name: string, topPeps: number[]}}
 */
dagcomponentfuncs.GroupBadges = function (props) {
    const { setData, value, colDef, groupInfo, data } = props;

    // ツールチップ用のstate
    const [tooltip, setTooltip] = React.useState({ visible: false, x: 0, y: 0, content: null });

    // 値が配列でない場合や空の場合
    if (!Array.isArray(value) || value.length === 0) {
        return React.createElement(
            'span',
            {
                style: {
                    color: '#999',
                    fontStyle: 'italic',
                    fontSize: '12px',
                }
            },
            '-'
        );
    }

    // detailフィールド名を決定
    const detailFieldName = colDef.field + '_detail';
    const detailData = data[detailFieldName] || {};

    // ツールチップを表示
    function showTooltip(e, groupId) {
        const info = groupInfo ? groupInfo[groupId] : null;
        const groupName = info && info.name ? info.name : 'Group ' + groupId;

        // 関連PEPを取得
        const relatedPeps = detailData[groupId] || [];
        const relatedPepsStr = relatedPeps.length > 0 ? relatedPeps.join(', ') : '-';

        // ラベルを決定（cited_by_groups か cites_groups か）
        const isCitedBy = colDef.field === 'cited_by_groups';
        const pepsLabel = isCitedBy ? 'Citing PEPs' : 'Cited PEPs';

        setTooltip({
            visible: true,
            x: e.clientX,
            y: e.clientY,
            content: { groupName: groupName, pepsLabel: pepsLabel, relatedPepsStr: relatedPepsStr }
        });
    }

    // ツールチップを非表示
    function hideTooltip() {
        setTooltip({ visible: false, x: 0, y: 0, content: null });
    }

    // バッジのスタイル
    const badgeStyle = {
        display: 'inline-block',
        padding: '0px 6px',
        margin: '1px 3px 1px 0',
        backgroundColor: '#E8E8E8',
        border: '1px solid #CCC',
        borderRadius: '10px',
        fontSize: '11px',
        cursor: 'pointer',
        color: '#333',
        whiteSpace: 'nowrap',
        lineHeight: '1.4',
    };

    // 各グループIDに対してバッジを作成
    const badges = value.map(function (groupId) {
        return React.createElement(
            'span',
            {
                key: groupId,
                style: badgeStyle,
                onClick: function (e) {
                    e.stopPropagation();
                    setData({
                        groupId: groupId,
                        field: colDef.field,
                    });
                },
                onMouseEnter: function (e) {
                    e.target.style.backgroundColor = '#D0D0D0';
                    showTooltip(e, groupId);
                },
                onMouseLeave: function (e) {
                    e.target.style.backgroundColor = '#E8E8E8';
                    hideTooltip();
                },
                onMouseMove: function (e) {
                    if (tooltip.visible) {
                        setTooltip(function (prev) {
                            return { ...prev, x: e.clientX, y: e.clientY };
                        });
                    }
                },
            },
            'G' + groupId
        );
    });

    // ツールチップ要素（React Portalでbodyに追加）
    const tooltipElement = tooltip.visible && tooltip.content
        ? ReactDOM.createPortal(
            React.createElement(
                'div',
                {
                    style: {
                        position: 'fixed',
                        left: tooltip.x + 10,
                        top: tooltip.y - 50,
                        backgroundColor: '#222',
                        color: 'white',
                        padding: '8px 10px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        whiteSpace: 'nowrap',
                        zIndex: 10000,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                        pointerEvents: 'none',
                    }
                },
                [
                    React.createElement(
                        'div',
                        {
                            key: 'name',
                            style: { fontWeight: 'bold', marginBottom: '4px' }
                        },
                        tooltip.content.groupName
                    ),
                    React.createElement(
                        'div',
                        {
                            key: 'peps',
                            style: { fontSize: '10px', color: '#aaa' }
                        },
                        tooltip.content.pepsLabel + ': ' + tooltip.content.relatedPepsStr
                    ),
                ]
            ),
            document.body
        )
        : null;

    return React.createElement(
        'div',
        {
            style: {
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                padding: '2px 0',
            }
        },
        [badges, tooltipElement]
    );
};
