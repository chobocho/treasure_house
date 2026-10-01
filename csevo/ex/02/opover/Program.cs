// 슬라이드 p2-v1-opover — 연산자 오버로딩, C# 1.0
using System;

struct Money
{
    long cents;
    public Money(long cents) { this.cents = cents; }

    public static Money operator +(Money a, Money b)
    {
        return new Money(a.cents + b.cents);
    }
    public static Money operator *(Money a, int n)
    {
        return new Money(a.cents * n);
    }
    public static Money operator -(Money a)
    {
        return new Money(-a.cents);
    }
    public static bool operator ==(Money a, Money b)
    {
        return a.cents == b.cents;
    }
    public static bool operator !=(Money a, Money b)
    {
        return !(a == b);
    }
    public override bool Equals(object o)
    {
        return o is Money && this == (Money)o;
    }
    public override int GetHashCode() { return cents.GetHashCode(); }
    public override string ToString()
    {
        long r = Math.Abs(cents % 100);
        return (cents / 100) + "." + r.ToString("00");
    }
}
