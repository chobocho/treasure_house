// 슬라이드 p8-v7_1-refasm — 참조 어셈블리에 남는 것, C# 7.1
public class Lib
{
    private int secret = 3;
    public int Add(int a, int b) { return a + b + Twice() - 6; }
    internal int Hidden() { return 1; }
    private int Twice() { return secret * 2; }
}

public struct Pair
{
    private int a;               // a struct's private field
    public Pair(int a) { this.a = a; }
    public int Get() { return a; }
}
