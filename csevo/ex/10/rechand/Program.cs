// 슬라이드 p10-v9-rec-hand — 명세의 '대략 이런 코드'를 손으로, C# 9.0
using System;
using System.Collections.Generic;
using System.Text;

class H : IEquatable<H>          // what 'record H(int P1)' means
{
    public int P1 { get; init; }
    public H(int P1) { this.P1 = P1; }
    protected virtual Type EqualityContract => typeof(H);
    public override bool Equals(object obj) => Equals(obj as H);
    public virtual bool Equals(H other) =>
        !(other is null) && EqualityContract == other.EqualityContract
        && EqualityComparer<int>.Default.Equals(P1, other.P1);
    public static bool operator ==(H l, H r)
        => (object)l == r || (l?.Equals(r) ?? false);
    public static bool operator !=(H l, H r) => !(l == r);
    public override int GetHashCode() => HashCode.Combine(
        EqualityComparer<Type>.Default.GetHashCode(EqualityContract),
        EqualityComparer<int>.Default.GetHashCode(P1));
    protected virtual bool PrintMembers(StringBuilder b)
    {
        b.Append(nameof(P1)).Append(" = ").Append(P1.ToString());
        return true;
    }
    public override string ToString()
    {
        var b = new StringBuilder().Append(nameof(H)).Append(" { ");
        if (PrintMembers(b)) b.Append(' ');
        return b.Append('}').ToString();
    }
}

record R(int P1);

class App
{
    static void Main()
    {
        Console.WriteLine(new H(1) + " " + (new H(1) == new H(1)));
        Console.WriteLine(new R(1) + " " + (new R(1) == new R(1)));
    }
}
