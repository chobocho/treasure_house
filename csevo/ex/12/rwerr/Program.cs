// 슬라이드 p12-v11-raw-errors — 원시 문자열의 규칙과 오류 번호, C# 11.0
class App
{
    static void Main()
    {
#if OPEN
        string a = """text on the opening line
            """;
#endif
#if CLOSE
        string b = """
            text""";
#endif
#if EMPTY
        string c = """
            """;
#endif
#if SIX
        string d = """""";
#endif
#if QUOTES
        string e = """ a """" b """;
#endif
#if UNDER
        string f = """
            ok
          under
            """;
#endif
#if TAB
        string g = """
	tab
            """;
#endif
    }
}
