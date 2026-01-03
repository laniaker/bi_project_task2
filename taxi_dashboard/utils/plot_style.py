def apply_exec_style(fig, title=None):
    """
    Einheitliches Executive-Layout für alle Plotly-Figures.
    Ziel: konsistentes Erscheinungsbild über alle Charts hinweg.
    """

    # Grundlayout: transparenter Hintergrund für nahtlose Einbettung in Cards
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",   # Hintergrund der gesamten Figure
        plot_bgcolor="rgba(0,0,0,0)",    # Hintergrund des Plot-Bereichs
        font=dict(
            family="Inter, system-ui, sans-serif",  # konsistente Typografie
            size=12,
            color="#0f172a",
        ),
        # Einheitliche Innenabstände für Titel, Achsen und Labels
        margin=dict(l=20, r=20, t=40, b=20),
        # Optionaler Titel: nur überschreiben, wenn explizit übergeben
        title=title if title is not None else fig.layout.title,
    )

    # Achsen-Styling: dezente Gridlines, keine dominante Nulllinie
    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.35)",
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.35)",
        zeroline=False,
    )
    return fig
