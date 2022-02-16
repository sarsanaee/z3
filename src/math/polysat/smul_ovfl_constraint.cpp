/*++
Copyright (c) 2021 Microsoft Corporation

Module Name:

    polysat multiplication overflow constraint

Author:

    Jakob Rath, Nikolaj Bjorner (nbjorner) 2021-12-09

--*/
#include "math/polysat/smul_ovfl_constraint.h"
#include "math/polysat/solver.h"

namespace polysat {

    smul_ovfl_constraint::smul_ovfl_constraint(constraint_manager& m, pdd const& p, pdd const& q):
        constraint(m, ckind_t::smul_ovfl_t), m_p(p), m_q(q) {
        simplify();
        m_vars.append(m_p.free_vars());
        for (auto v : m_q.free_vars())
            if (!m_vars.contains(v))
                m_vars.push_back(v);

    }
    void smul_ovfl_constraint::simplify() {
        if (m_p.is_zero() || m_q.is_zero() ||
            m_p.is_one() || m_q.is_one()) {
            m_q = 0;
            m_p = 0;
            return;
        }
        if (m_p.index() > m_q.index())
            std::swap(m_p, m_q);
    }

    std::ostream& smul_ovfl_constraint::display(std::ostream& out, lbool status) const {
        switch (status) {
        case l_true: return display(out);
        case l_false: return display(out << "~");
        case l_undef: return display(out << "?");
        }       
        return out;
    }

    std::ostream& smul_ovfl_constraint::display(std::ostream& out) const {
        return out << "sovfl*(" << m_p << ", " << m_q << ")";       
    }

    void smul_ovfl_constraint::narrow(solver& s, bool is_positive, bool first) {
        if (!first)
            return;
        signed_constraint sc(this, is_positive);
        if (is_positive) {
            s.add_clause(~sc, s.ule(2, p()), false);
            s.add_clause(~sc, s.ule(2, q()), false);
            s.add_clause(~sc, ~s.sgt(p(), 0), s.sgt(q(), 0), false);
            s.add_clause(~sc, ~s.sgt(q(), 0), s.sgt(p(), 0), false);
            s.add_clause(~sc, ~s.sgt(p(), 0), s.slt(p()*q(), 0), s.mul_ovfl(p(), q()), false);
            s.add_clause(~sc, s.sgt(p(), 0),  s.slt(p()*q(), 0), s.mul_ovfl(-p(), -q()), false);
        }
        else {
            // smul_noovfl(p,q) => sign(p) != sign(q) or p'*q' < 2^{K-1}
            s.add_clause(~sc, ~s.sgt(p(), 0), ~s.sgt(q(), 0), ~s.mul_ovfl(p(), q()), false);
            s.add_clause(~sc, ~s.sgt(p(), 0), ~s.sgt(q(), 0), ~s.slt(p()*q(), 0), false);
            s.add_clause(~sc, ~s.slt(p(), 0), ~s.slt(q(), 0), ~s.mul_ovfl(-p(), -q()), false);
            s.add_clause(~sc, ~s.slt(p(), 0), ~s.slt(q(), 0), ~s.slt((-p())*(-q()), 0), false);
        }
    }

    unsigned smul_ovfl_constraint::hash() const {
    	return mk_mix(p().hash(), q().hash(), kind());
    }

    bool smul_ovfl_constraint::operator==(constraint const& other) const {
        return other.is_smul_ovfl() && p() == other.to_smul_ovfl().p() && q() == other.to_smul_ovfl().q();
    }
}
