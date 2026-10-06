// 슬라이드 p14-sum-codes — 버전마다 다른 '없는 기능' 번호, C# 14
class P
{
    int N;

    static void Main()
    {
        P p = new P();
        p?.N = 41;                    // null-conditional assignment
        System.Console.WriteLine(p.N + 1);
    }
}
