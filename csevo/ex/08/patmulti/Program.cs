// 슬라이드 p8-v7-pat-multi — 한 구역에 case 둘, C# 7.0
class App
{
    static int M(object o)
    {
        switch (o)
        {
            case int n:
            case long n2:
                return n;                   // which label matched?
            case string s when s.Length > 0:
            case string s2:
                return 0;
        }
        return -1;
    }

    static void Main() { }
}
